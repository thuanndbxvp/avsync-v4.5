"""domain.visual_style — Visual Style Profile parsing (pure, no I/O).

Di chuyển từ `ai_prompts.py` (Milestone 1 refactor).
Pure JSON/text manipulation — không gọi API, không đọc file.
"""
from __future__ import annotations

import json
import re
from typing import Any


# ---------------------------------------------------------------------------
# Field name dictionaries (normalize substring để match nhiều biến thể tên)
# ---------------------------------------------------------------------------
_CAPTION_FIELDS: tuple[str, ...] = (
    "art_style", "artstyle", "art_direction", "line_work", "linework",
    "lineart", "outline", "shading_lighting", "shading", "rendering",
    "render_style", "aesthetic", "full_prompt", "full_style_tag", "style_tag",
)
_MOOD_FIELDS: tuple[str, ...] = ("mood", "tone", "atmosphere")
_AI_FIELDS: tuple[str, ...] = (
    "scene_mode", "scenes", "color_palette", "colour_palette", "colors",
    "colours", "palette", "characters", "character", "variety", "composition",
    "camera",
)


def _norm_key(k: Any) -> str:
    return str(k).lower().replace("-", "_").replace(" ", "_")


norm_key = _norm_key  # alias public (để các module khác dùng)


# ---------------------------------------------------------------------------
# JSON / dict helpers
# ---------------------------------------------------------------------------
def as_json(style: str):
    """Thử parse Style Profile dạng JSON dict; không phải JSON thì trả None."""
    try:
        d = json.loads(style)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def scene_modes_present(style: str) -> bool:
    d = as_json(style)
    return bool(d and isinstance(d.get("scene_modes"), dict) and d["scene_modes"])


def scene_mode_keys(style: str) -> list[str]:
    d = as_json(style)
    if d and isinstance(d.get("scene_modes"), dict):
        return list(d["scene_modes"].keys())
    return []


def character_keys(style: str) -> list[str]:
    """Tên KEY trong 'characters' (vd modern_human, ancient_human)."""
    d = as_json(style)
    if d and isinstance(d.get("characters"), dict):
        return list(d["characters"].keys())
    return []


# ---------------------------------------------------------------------------
# Flatten dict/list/scalar lồng nhau thành text
# ---------------------------------------------------------------------------
def to_text(obj: Any) -> str:
    """Làm phẳng dict/list/scalar lồng nhau thành text đọc được (bỏ tên key)."""
    if isinstance(obj, bool):
        return ""
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        return ", ".join(t for t in (to_text(x) for x in obj) if t)
    if isinstance(obj, dict):
        return "; ".join(t for t in (to_text(v) for v in obj.values()) if t)
    return ""


def deep_collect(obj: Any, names: tuple[str, ...]) -> list[str]:
    """Duyệt ĐỆ QUY: mỗi key khớp tên (substring sau norm) -> lấy text value 1 lần,
    không đi sâu vào key đã khớp. Nhờ vậy field lồng mấy lớp cũng moi ra được."""
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(n in _norm_key(k) for n in names):
                t = to_text(v)
                if t:
                    out.append(t)
            else:
                out.extend(deep_collect(v, names))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(deep_collect(v, names))
    return out


# ---------------------------------------------------------------------------
# ART-STYLE caption (câu cố định ghép vào mọi prompt)
# ---------------------------------------------------------------------------
def style_caption(style: str) -> str:
    """Câu ART-STYLE CỐ ĐỊNH (text) để TOOL tự ghép vào MỌI prompt.

    ROBUST: đọc được MỌI cấu trúc JSON — tìm sâu các field nét (kể cả lồng / tên lạ),
    và nếu không khớp tên nào thì FALLBACK làm phẳng cả JSON -> KHÔNG BAO GIỜ rỗng.
    Profile text thuần -> dùng nguyên văn.
    """
    s = (style or "").strip()
    if not s:
        return ""
    d = as_json(s)
    if d is None:
        return s  # text thuần -> dùng nguyên
    parts = deep_collect(d, _CAPTION_FIELDS)  # gom phần NÉT (tìm sâu)
    mood = deep_collect(d, _MOOD_FIELDS)
    if mood:
        parts.append("overall mood: " + mood[0])
    if not parts:
        # FALLBACK: JSON cấu trúc lạ -> làm phẳng toàn bộ (bỏ phần động scene/character)
        skip = ("scene_mode", "scenes", "character")
        leftover = {
            k: v for k, v in d.items()
            if not any(x in _norm_key(k) for x in skip)
        }
        flat = to_text(leftover or d)
        return flat
    parts = [p.rstrip(" .") for p in parts if p.strip()]
    parts = [(p[:1].upper() + p[1:]) for p in parts]  # viết hoa đầu mỗi vế
    cap = ". ".join(parts)
    return (cap + ".") if cap else ""


def style_caption_is_empty(style: str) -> bool:
    """True nếu profile KHÔNG sinh được caption nét nào."""
    return not style_caption(style).strip()


# ---------------------------------------------------------------------------
# Style gửi cho AI: giữ field NỘI DUNG, bỏ field NÉT
# ---------------------------------------------------------------------------
def style_for_ai(style: str) -> str:
    """Style gửi cho AI: giữ field NỘI DUNG (scene_modes/characters/variety/màu...),
    bỏ field NÉT (AI bị cấm tả)."""
    d = as_json(style)
    if d is None:
        return (style or "").strip()
    keep = {
        k: v for k, v in d.items()
        if any(n in _norm_key(k) for n in _AI_FIELDS)
    }
    return json.dumps(keep, ensure_ascii=False) if keep else (style or "").strip()


# ---------------------------------------------------------------------------
# Strip mode keys (nếu AI lỡ in nguyên tên key scene_mode vào câu)
# ---------------------------------------------------------------------------
def strip_mode_keys(text: str, keys: list[str]) -> str:
    """Đổi '_' trong tên key scene_mode (vd 'ancient_day') -> khoảng trắng để đọc được.
    Chỉ xử lý key CÓ dấu '_' để khỏi đụng các từ thường."""
    for k in keys:
        if "_" in k:
            text = re.sub(r"\b" + re.escape(k) + r"\b", k.replace("_", " "), text)
    return text