"""Smoke test Milestone 3: domain.render_plan + infrastructure.ffmpeg_client +
services.render_service + auto_edit.render_video Strangler.

Tests 2 layers:
  1. PURE (no ffmpeg) — domain.render_plan (ScenePlan, plan_scenes, choose_fps, ...)
  2. WIRE (real or mocked) — services.render_service wired through auto_edit.render_video
"""
import os
import sys
import tempfile
import importlib
import csv

sys.path.insert(0, r"d:\auto-edit-video-main")

# ---------- Test 1: imports ----------
from domain.render_plan import (
    ScenePlan, RenderPlan, plan_scenes, choose_fps, choose_encoder_jobs,
    apply_max_scenes, derive_total_end, normalize_aspect,
    DEFAULT_IMAGE_EXTS, DEFAULT_VIDEO_EXTS,
)
import infrastructure.ffmpeg_client as fclient
import services.render_service as rs
import auto_edit as ae
print("[OK] domain.render_plan + infrastructure.ffmpeg_client + services.render_service imports")

# ---------- Test 2: ScenePlan dataclass ----------
sp = ScenePlan(source="/tmp/a.png", duration=2.5)
assert sp.source == "/tmp/a.png"
assert sp.duration == 2.5
assert sp.is_image is True
assert sp.is_video is False
sp_v = ScenePlan(source="/tmp/a.mp4", duration=4.0)
assert sp_v.is_video is True
print("[OK] ScenePlan dataclass + is_image/is_video")

# ---------- Test 3: RenderPlan dataclass ----------
rp = RenderPlan()
assert rp.fps == 30
assert rp.aspect == "16:9"
assert rp.has_video is False
assert rp.has_audio_mix is False
rp.scenes = [sp, sp_v]
assert rp.has_video is True
assert rp.has_audio_mix is False
rp.logo_path = "/tmp/logo.png"
assert rp.has_audio_mix is True
print("[OK] RenderPlan dataclass + has_video/has_audio_mix")

# ---------- Test 4: plan_scenes (pure) ----------
segs = [
    {"start": 0.0, "end": 2.0, "text": "hi"},
    {"start": 2.0, "end": 4.0, "text": "there"},
    {"start": 4.0, "end": 6.0, "text": "world"},
]
media = [f"img_{i}.png" for i in range(3)]

# mode auto: 3 images == 3 segs -> srt
scenes, label = plan_scenes(segs=segs, media=media, total_end=6.0,
                            mode="auto", n_img=3, n_seg=3)
assert len(scenes) == 3
assert "1 ảnh / 1 đoạn" in label or "srt" in label.lower()
assert scenes[0].source == "img_0.png"
assert scenes[0].duration == 2.0
print("[OK] plan_scenes auto -> srt (3 images == 3 segs)")

# mode auto: 1 image, 3 segs -> spread
scenes, label = plan_scenes(segs=segs, media=["only.png"], total_end=6.0,
                            mode="auto", n_img=1, n_seg=3)
assert len(scenes) == 1
assert scenes[0].duration == 6.0
assert "rải đều" in label
print("[OK] plan_scenes auto -> spread (1 image vs 3 segs)")

# mode seconds_per_image
scenes, label = plan_scenes(segs=segs, media=media, total_end=10.0,
                            mode="srt", seconds_per_image=2.0, n_img=3, n_seg=3)
assert len(scenes) == 5, f"Expected 5 scenes (10/2), got {len(scenes)}"
assert scenes[0].duration == 2.0
assert "mỗi ảnh ~2s" in label
print("[OK] plan_scenes seconds_per_image")

# ---------- Test 5: choose_fps ----------
scenes_imgs = [ScenePlan(source=f"img_{i}.png", duration=2.0) for i in range(3)]
fps, why = choose_fps(scenes_imgs, requested_fps=24)
assert fps == 24 and "fps" in why
print("[OK] choose_fps explicit")

fps, why = choose_fps(scenes_imgs)
assert fps == 30 and "ảnh tĩnh" in why
print("[OK] choose_fps default (toàn ảnh -> 30)")

scenes_mix = [ScenePlan(source="img.png", duration=2.0),
              ScenePlan(source="clip.mp4", duration=3.0)]
fps, why = choose_fps(scenes_mix)
assert fps == 24, f"Expected 24 (clip Veo), got {fps}"
print("[OK] choose_fps với video -> 24")

# ---------- Test 6: choose_encoder_jobs ----------
enc, jobs = choose_encoder_jobs("libx264", cpu_count=8, requested_jobs=2)
assert enc == "libx264" and jobs == 2
print("[OK] choose_encoder_jobs explicit")

enc, jobs = choose_encoder_jobs("libx264", cpu_count=8)
assert enc == "libx264" and jobs == 4, f"Expected 4 (8/2), got {jobs}"
print("[OK] choose_encoder_jobs auto (cpu=8 -> 4)")

enc, jobs = choose_encoder_jobs("h264_nvenc", cpu_count=8)
assert jobs <= 3, f"GPU encoder should cap at 3, got {jobs}"
print("[OK] choose_encoder_jobs GPU cap")

# ---------- Test 7: apply_max_scenes ----------
scenes = [ScenePlan(source=f"img_{i}.png", duration=2.0) for i in range(10)]
scenes, total, label = apply_max_scenes(scenes, 3, 20.0)
assert len(scenes) == 3
assert total == 6.0
assert "XEM TRƯỚC" in label
print("[OK] apply_max_scenes cuts to N")

scenes, total, label = apply_max_scenes(scenes, 100, 20.0)
assert len(scenes) == 3  # unchanged
assert total == 20.0     # unchanged
assert label == ""
print("[OK] apply_max_scenes no-op when scenes < max")

# ---------- Test 8: derive_total_end ----------
assert derive_total_end(segs, None) == 6.0
assert derive_total_end(segs, 10.0) == 10.0   # audio wins
assert derive_total_end(segs, 4.0) == 6.0     # segs wins
assert derive_total_end([], 5.0) == 0.0
print("[OK] derive_total_end (max(segs, audio))")

# ---------- Test 9: normalize_aspect ----------
w, h = normalize_aspect("16:9")
assert (w, h) == (1920, 1080)
w, h = normalize_aspect("9:16")
assert (w, h) == (1080, 1920)
print("[OK] normalize_aspect")

# ---------- Test 10: backward-compat auto_edit.render_video ----------
# Render_video should be a shim (~10 lines), still callable
src = importlib.import_module("auto_edit")
assert callable(src.render_video)
import inspect
source = inspect.getsource(src.render_video)
lines = len(source.splitlines())
assert lines <= 15, f"render_video should be a shim (≤15 lines), got {lines}"
assert "services.render_service" in source
print(f"[OK] auto_edit.render_video is shim ({lines} lines)")

# ---------- Test 11: services.render_service has orchestration ----------
assert callable(rs.render_video)
assert callable(rs._build_args)
# Check signature compat
import inspect
sig = inspect.signature(rs.render_video)
params = list(sig.parameters.keys())
assert params[:4] == ["srt_path", "img_dir", "out_path", "cfg"], f"Bad signature: {params}"
assert "progress_cb" in params
print("[OK] services.render_service.render_video signature compat")

# ---------- Test 12: _build_args namespace ----------
args = rs._build_args("a.srt", "img/", "out.mp4", {"dry_run": True, "aspect": "9:16"})
assert args.srt == "a.srt"
assert args.images == "img/"
assert args.out == "out.mp4"
assert args.dry_run is True
assert args.aspect == "9:16"
# defaults
assert args.image_mode == "auto"
assert args.clip_fit == "auto"
assert args.fps is None
print("[OK] _build_args builds SimpleNamespace from cfg")

# ---------- Test 13: ffmpeg_client public API ----------
assert callable(fclient.build_clip)
assert callable(fclient.concat_or_xfade)
assert callable(fclient.build_master_clip)
assert callable(fclient.compose_final)
assert callable(fclient.run_ffmpeg)
print("[OK] ffmpeg_client public API surface")

# ---------- Test 14: render_video calls with dry_run (no ffmpeg) ----------
# dry_run returns True BEFORE running ffmpeg — safe to call without real ffmpeg.
# Bug compat: original render_video calls find_voice(args.input_dir) before dry_run
# branch checks, so we must create a dummy input_dir.
testdir = tempfile.mkdtemp(prefix="m3_test_")
try:
    srt_path = os.path.join(testdir, "test.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("1\n00:00:01,000 --> 00:00:03,500\nHello\n\n2\n00:00:04,000 --> 00:00:07,000\nWorld\n")
    img_dir = os.path.join(testdir, "images")
    os.makedirs(img_dir, exist_ok=True)
    input_dir = os.path.join(testdir, "input")
    os.makedirs(input_dir, exist_ok=True)
    # Create 2 dummy PNGs
    for i in range(2):
        import base64
        with open(os.path.join(img_dir, f"img_{i}.png"), "wb") as f:
            f.write(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQI12P4//8/AwAI/AL+XJ8H6wAAAABJRU5ErkJggg=="
            ))
    out_path = os.path.join(testdir, "out.mp4")

    logs = []
    result = ae.render_video(srt_path, img_dir, out_path,
                              cfg={"dry_run": True, "image_mode": "srt",
                                   "input_dir": input_dir},
                              progress_cb=logs.append)
    assert result is True, f"dry_run should return True, got {result}"
    assert any("cảnh" in s for s in logs), f"Expected scene log, got: {logs}"
    print(f"[OK] render_video dry_run returns True ({len(logs)} log lines)")
finally:
    import shutil
    shutil.rmtree(testdir, ignore_errors=True)

# ---------- Test 15: workers + UI still import ----------
import importlib
for mod in [
    "core.worker_render", "core.worker_prompt",
    "core.worker_sleep", "core.worker_queue",
    "ui.main_window", "ui.tabs.tab_prompt",
    "build_scenes", "ai_prompts",
]:
    importlib.import_module(mod)
print("[OK] core/worker_* + ui/main_window + ui/tabs + build_scenes + ai_prompts all import")

# ---------- Test 16: M1 + M1.5 + M2 backward-compat ----------
from domain.timeline import parse_srt, group_scenes, _ends_with_punctuation
assert _ends_with_punctuation("Hi.") is True
segs5 = parse_srt(r"d:\auto-edit-video-input\test_milestone1.srt")
scenes5 = group_scenes(segs5, 8.0)
assert len(scenes5) >= 1
print("[OK] M1 + M1.5 backward-compat (parse_srt, group_scenes)")

from infrastructure.ai_pool import AsyncAIPool
assert AsyncAIPool(5).max_concurrent == 5
print("[OK] M2 backward-compat (AsyncAIPool)")

# ---------- Test 17: domain.render_plan exports ----------
from domain.render_plan import (
    ScenePlan as _SP, RenderPlan as _RP, plan_scenes as _ps,
    choose_fps as _cf, choose_encoder_jobs as _cj,
)
assert _SP is ScenePlan
assert _RP is RenderPlan
assert _ps is plan_scenes
print("[OK] domain.render_plan full export surface")

print("\n=== ALL MILESTONE 3 TESTS PASSED ===")