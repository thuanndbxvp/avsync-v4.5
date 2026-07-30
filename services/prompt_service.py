"""services.prompt_service — orchestration cho use case 'generate prompts'.

Move logic `_run_batches` từ `ai_prompts.py` sang đây và CHUYỂN SANG ASYNC:
  - Mỗi batch (8-25 cảnh tuỳ provider) được dispatch 1 task asyncio.
  - AsyncAIPool giới hạn số batch chạy cùng lúc (semaphore) → tránh rate-limit 429.
  - Tất cả network I/O (gọi AI) chạy trong `asyncio.to_thread()` → không block loop.

GIỮ NGUYÊN behavior retry/đổi model: mỗi batch vẫn tự thử 4 lần, đổi model nếu
429/404/500/503 — chỉ là các batch SONG SONG với nhau.

Strangler (tương thích ngược): `ai_prompts.generate_prompts(...)` cũ vẫn là sync
function — giờ làm 1 wrapper gọi `asyncio.run(generate_prompts_async(...))`.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from typing import Callable, Optional

from domain.visual_style import (
    style_caption as _style_caption,
    style_for_ai as _style_for_ai,
    scene_mode_keys as _scene_mode_keys,
    scene_modes_present as _scene_modes_present,
    character_keys as _character_keys,
    strip_mode_keys as _strip_mode_keys,
)
from infrastructure.ai_pool import AsyncAIPool


# ─── HẰNG SỐ — trỏ về ai_prompts để không duplicate ────────────────────────────
def _get_provider_consts():
    """Lazy import provider/model constants from ai_prompts to avoid circular dep."""
    import ai_prompts as ap
    return ap.SYSTEM_SPLIT_VIDEO, ap.SYSTEM_SPLIT_IMAGE, ap.SYSTEM_CONTENT_VIDEO, ap.SYSTEM_CONTENT_IMAGE, ap.SYSTEM_MOTION, ap.SYSTEM_CHAIN_MOTION, ap.SYSTEM_QC, ap.MODELS, ap.DEFAULT_BATCH, ap.GeminiError, ap._call, ap._friendly, ap._parse_array, ap._inject_character, ap._title_context


# ─── CORE ASYNC: 1 batch AI call (keeps retry/logic giống _run_batches cũ) ────────
async def _call_batch_async(
    provider: str, api_key: str, model_preferred: Optional[str],
    system: str, chunk: list[str], previous_tail: Optional[list[str]] = None,
    timeout: float = 120.0, max_retries: int = 4,
) -> list[str]:
    """Gọi AI 1 batch (sequential nội bộ: retry + model fallback giống cũ).

    Tham khảo hàm cũ trong ai_prompts._run_batches: mỗi batch tự thử 4 lần,
    mỗi lần đổi model nếu 429/404/500/503. Kết quả trả list[str] độ dài = len(chunk).
    """
    SYSTEM_SPLIT_VIDEO, SYSTEM_SPLIT_IMAGE, SYSTEM_CONTENT_VIDEO, SYSTEM_CONTENT_IMAGE, \
        SYSTEM_MOTION, SYSTEM_CHAIN_MOTION, SYSTEM_QC, MODELS, DEFAULT_BATCH, \
        GeminiError, _call, _friendly, _parse_array, _inject_character, _title_context = _get_provider_consts()

    pref = MODELS.get(provider, MODELS["gemini"])
    order = ([model_preferred] if model_preferred else []) + \
            [m for m in pref if m != model_preferred]
    chosen: Optional[str] = None
    last_exc: Optional[Exception] = None

    n = len(chunk)
    listing = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(chunk))
    user = (f"Here are {n} scenes. Write one prompt for each, "
            f"returning a JSON array of exactly {n} strings, in order.\n\n{listing}")
    if previous_tail:
        tail = [p for p in previous_tail if (p or "").strip()]
        if tail:
            prev = "\n".join(f"- {p}" for p in tail)
            user = (f"CONTEXT — the prompts for the scenes immediately BEFORE these "
                    f"(already written) were:\n{prev}\n"
                    f"Continue the variety: do NOT open with the same shot type or "
                    f"camera move as those.\n\n{user}")

    for attempt in range(max_retries):
        models_try = ([chosen] if chosen else []) + [m for m in order if m != chosen]
        txt: Optional[str] = None
        for m in models_try:
            try:
                # Wrap sync urllib call in to_thread → non-blocking cho event loop
                txt = await asyncio.to_thread(_call, provider, api_key, m, system, user, timeout)
                chosen = m
                break
            except GeminiError as e:
                last_exc = e
                if e.code in (404, 429, 500, 503):
                    continue
                raise RuntimeError(_friendly(e))
        if txt is None:
            chosen = None
            await asyncio.sleep(2 * (attempt + 1))
            continue
        candidate = _parse_array(txt, n)
        empty_idx = [i + 1 for i, p in enumerate(candidate) if not p.strip()]
        if not empty_idx or attempt == max_retries - 1:
            if empty_idx:
                print(f"  ⚠️  Batch cảnh (async): "
                      f"prompt RỖNG tại vị trí {empty_idx} (hết retry)", file=sys.stderr)
            return candidate
        print(f"  ⚠️  Batch cảnh (async): "
              f"prompt RỖNG tại vị trí {empty_idx}, retry ({attempt + 1}/{max_retries-1})...",
              file=sys.stderr)
        await asyncio.sleep(2)
    raise RuntimeError(_friendly(last_exc) if last_exc else "Không sinh được prompt.")


# ─── ORCHESTRATOR ASYNC: chia batch, dispatch SONG SONG qua AsyncAIPool ────────
async def _run_batches_async(
    system: str, scenes_text: list[str],
    api_key: str, model: Optional[str],
    batch: int, progress: Optional[Callable[[int, int], None]],
    provider: str = "gemini",
    pool: Optional[AsyncAIPool] = None,
) -> list[str]:
    """Run _call_batch_async cho từng batch — CÁC BATCH SONG SONG (gather).

    Khác với code cũ (chỉ 1 batch tại 1 thời điểm, tuần tự), code mới dispatch
    tất cả batch đồng thời (giới hạn bởi pool.max_concurrent) -> AI 5x-10x nhanh
    hơn tuỳ AI provider rate-limit.
    """
    _, _, _, _, _, _, _, MODELS, DEFAULT_BATCH, _, _, _, _, _, _ = _get_provider_consts()

    pool = pool or AsyncAIPool(max_concurrent=5)
    n = len(scenes_text)
    if n == 0:
        return []
    chunks: list[tuple[int, list[str]]] = []
    for start in range(0, n, batch):
        chunks.append((start, scenes_text[start:start + batch]))
    # Lưu previous_tail ngay trước khi dispatch (dùng shared list)
    done_lock = asyncio.Lock()
    out: list[Optional[str]] = [None] * n
    progress_done = 0
    last_chosen_model: dict = {"m": model}   # share giữa các batch (giống cũ)

    async def _one(idx: int, start: int, chunk: list[str]):
        # Lấy tail 2 prompt cuối của batch trước (chỉ xem reference, không strict)
        prev_tail = None
        async with done_lock:
            if start > 0:
                prev_tail = [out[j] for j in range(max(0, start - 2), start) if out[j]]
        result = await _call_batch_async(
            provider, api_key, last_chosen_model["m"],
            system, chunk, previous_tail=prev_tail,
        )
        for i, p in enumerate(result):
            out[start + i] = p
        nonlocal_progress = 0
        async with done_lock:
            nonlocal progress_done
            progress_done += len(chunk)
            nonlocal_progress = progress_done
        if progress:
            progress(min(nonlocal_progress, n), n)
        return start, result

    tasks = [pool.gather([_one(i, s, c) for i, (s, c) in enumerate(chunks)])]
    started_chunks = await asyncio.gather(*tasks)
    return [(p or "") for p in out]


# ─── HIGH-LEVEL ASYNC API (chạy được từ workers/UI) ──────────────────────────────
async def generate_prompts_async(
    scenes_text, style, api_key, model=None,
    batch=None, progress=None, mode="video", embed_style=True,
    style_mode=None, provider="gemini", character="", title="",
):
    """Async version of ai_prompts.generate_prompts. Cùng chữ ký, cùng output."""
    _, _, SYSTEM_CONTENT_VIDEO, SYSTEM_CONTENT_IMAGE, _, _, _, MODELS, DEFAULT_BATCH, \
        GeminiError, _, _, _, _, _ = _get_provider_consts()

    if not api_key or not api_key.strip():
        raise RuntimeError("Chưa nhập API key (vào tab Cài đặt).")
    if batch is None:
        batch = DEFAULT_BATCH.get(provider, 12)
    if style_mode is None:
        style_mode = "in_prompt" if embed_style else "lock_all"
    if style_mode == "in_prompt" and (not style or not style.strip()):
        raise RuntimeError("Chưa có Style Profile (vào tab Cài đặt để thêm/chọn).")

    api_key = api_key.strip()
    caption = ""
    mode_keys = _scene_mode_keys(style)
    has_modes = _scene_modes_present(style)
    if style_mode == "lock_all":
        system = SYSTEM_CONTENT_IMAGE if mode == "image" else SYSTEM_CONTENT_VIDEO
    else:
        from ai_prompts import SYSTEM_SPLIT_VIDEO, SYSTEM_SPLIT_IMAGE  # template constants
        if style_mode == "lock_art":
            template = SYSTEM_SPLIT_IMAGE if mode == "image" else SYSTEM_SPLIT_VIDEO
        else:
            template = SYSTEM_SPLIT_IMAGE if mode == "image" else SYSTEM_SPLIT_VIDEO
        if has_modes:
            system = template.format(style=_style_for_ai(style))
        else:
            system = SYSTEM_CONTENT_IMAGE if mode == "image" else SYSTEM_CONTENT_VIDEO
        if style_mode == "in_prompt":
            caption = _style_caption(style)
    from ai_prompts import _inject_character, _title_context
    system = _inject_character(system, character)
    system = _title_context(title) + system

    out = await _run_batches_async(
        system, scenes_text, api_key, model, batch, progress, provider,
    )

    leak_keys = mode_keys + _character_keys(style)
    result = []
    for p in out:
        p = _strip_mode_keys((p or "").strip(), leak_keys)
        if caption and p:
            p = f"{caption} {p}"
        result.append(p)
    return result


async def generate_motion_prompts_async(
    scenes_text, api_key, image_prompts=None, model=None, batch=None,
    progress=None, provider="gemini", character="", title="",
):
    """Async version of ai_prompts.generate_motion_prompts."""
    _, _, _, _, SYSTEM_MOTION, _, _, _, DEFAULT_BATCH, \
        GeminiError, _, _, _, _, _ = _get_provider_consts()

    if not api_key or not api_key.strip():
        raise RuntimeError("Chưa nhập API key (vào tab Cài đặt).")
    if batch is None:
        batch = DEFAULT_BATCH.get(provider, 12)
    api_key = api_key.strip()
    if image_prompts:
        feed = []
        for i, narr in enumerate(scenes_text):
            img = ((image_prompts[i] if i < len(image_prompts) else "") or "").strip()
            if img:
                feed.append(f"NARRATION: {narr}\n   KEYFRAME IMAGE (already drawn — animate THIS "
                            f"exact image, do not add anything not shown): {img}")
            else:
                feed.append(f"NARRATION: {narr}")
    else:
        feed = scenes_text
    char = (f'If the main character "{character.strip()}" appears, you may use the name in '
            f"the action.") if (character and character.strip()) else ""
    from ai_prompts import _title_context
    system = _title_context(title) + SYSTEM_MOTION.format(char=char)
    out = await _run_batches_async(
        system, feed, api_key, model, batch, progress, provider,
    )
    return [(p or "").strip() for p in out]


# ─── SYNC WRAPPERS (Strangler pattern cho code sync cũ) ────────────────────────
def generate_prompts(*args, **kwargs):
    """Sync shim — gọi asyncio.run(...) trên hàm async. Tương thích ngược.

    Worker sync (core/worker_prompt.py chạy trong QThread) vẫn gọi hàm này
    y hệt như trước, không cần thay đổi gì.
    """
    return asyncio.run(generate_prompts_async(*args, **kwargs))


def generate_motion_prompts(*args, **kwargs):
    return asyncio.run(generate_motion_prompts_async(*args, **kwargs))


def generate_chain_prompts(
    scenes_text, style, api_key, model=None, batch=None,
    progress=None, style_mode=None, provider="gemini",
    character="", title="",
):
    """Sync shim cho chain prompts (sequential 2 calls: image + motion)."""
    return asyncio.run(_generate_chain_prompts_async(
        scenes_text, style, api_key, model, batch, progress,
        style_mode, provider, character, title,
    ))


async def _generate_chain_prompts_async(
    scenes_text, style, api_key, model, batch, progress, style_mode,
    provider, character, title,
):
    """N image prompts (N+1) + N motion prompts — cũ vẫn tuần tự cho chain (phụ thuộc data)."""
    n = len(scenes_text)
    if n == 0:
        return [], []
    if batch is None:
        _, _, _, _, _, _, _, _, DEFAULT_BATCH, *_ = _get_provider_consts()
        batch = DEFAULT_BATCH.get(provider, 12)

    feed_img = [f"[Keyframe in ONE continuous story — SAME characters and setting throughout. "
                f"OPENING moment of scene {i + 1} of {n}] {narr}"
                for i, narr in enumerate(scenes_text)]
    feed_img.append(f"[Keyframe in ONE continuous story — SAME characters and setting. FINAL "
                    f"closing moment, right after scene {n}] {scenes_text[-1]}")
    img_prompts = await generate_prompts_async(
        feed_img, style, api_key, model=model, batch=batch,
        progress=progress, mode="image", style_mode=style_mode,
        provider=provider, character=character, title=title,
    )
    feed_motion = []
    for i in range(n):
        a = (img_prompts[i] if i < len(img_prompts) else "").strip()
        b = (img_prompts[i + 1] if i + 1 < len(img_prompts) else "").strip()
        feed_motion.append(f"NARRATION: {scenes_text[i]}\n   START FRAME: {a}\n   END FRAME: {b}")
    motion = await generate_motion_prompts_async(
        feed_motion, api_key, image_prompts=None, model=model, batch=batch,
        progress=progress, provider=provider, character=character, title=title,
    )
    return img_prompts, motion


def qc_scene_match(scenes, api_key, model=None, provider="gemini",
                   batch=25, progress=None):
    """Sync shim cho QC (M2 không bắt buộc async). Inline lại logic cũ — delegate
    sang ai_prompts cũ nếu còn, fallback inline impl."""
    import json as _json
    import re as _re
    _, _, _, _, _, _, SYSTEM_QC, MODELS, _, GeminiError, _call, _friendly, *_ = _get_provider_consts()
    if not api_key or not api_key.strip():
        raise RuntimeError("Chưa nhập API key (vào tab Cài đặt).")
    api_key = api_key.strip()
    pref = MODELS.get(provider, MODELS["gemini"])
    order = ([model] if model else []) + [m for m in pref if m != model]
    out, chosen, n = [], None, len(scenes)
    for start in range(0, n, batch):
        chunk = scenes[start:start + batch]
        listing = "\n".join(
            f'{s["scene"]}. NARRATION: {s["text"]}\n   IMAGE: {s["prompt"]}' for s in chunk)
        user = f"Judge these scenes:\n\n{listing}"
        txt, last = None, None
        models_try = ([chosen] if chosen else []) + [m for m in order if m != chosen]
        for m in models_try:
            try:
                txt = _call(provider, api_key, m, SYSTEM_QC, user)
                chosen = m
                break
            except GeminiError as e:
                last = e
                if e.code in (404, 429, 500, 503):
                    continue
                raise RuntimeError(_friendly(e))
        if txt is None:
            raise RuntimeError(_friendly(last) if last else "QC lỗi.")
        mt = _re.search(r"\[.*\]", txt, _re.S)
        if mt:
            try:
                out += _json.loads(mt.group(0))
            except Exception:
                pass
        if progress:
            progress(min(start + batch, n), n)
    return out