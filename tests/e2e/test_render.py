"""E2E Test: render_video() thực sự chạy ffmpeg từ SRT + ảnh/clip → MP4.

Mục đích: xác nhận pipeline render end-to-end (Stage 1: plan → Stage 2: gather clips →
Stage 3: master concat → Stage 4: final) KHÔNG bị break khi qua các refactor M1-M10.

Gọi trực tiếp `services.render_service.render_video()` (sync, không qua QThread)
để test nhanh + readable error.

REQUIREMENTS:
  - ffmpeg ở PATH
  - tests/e2e/data/dummy.srt + bg.jpg (auto-tạo qua _make_fixtures.py)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# Ensure fixtures exist
from tests.e2e._make_fixtures import write_srt, write_bg

DATA_DIR = os.path.join(HERE, "data")
SRT_FILE = write_srt()
BG_FILE = write_bg()
OUTPUT = os.path.join(HERE, "output.mp4")


def test_full_render():
    """Render full pipeline với 1 ảnh nền + 1 SRT fixture 7 giây."""
    if os.path.isfile(OUTPUT):
        os.remove(OUTPUT)

    cfg = {
        "aspect":  "16:9",
        "effect":  "none",
        "fps":     "30",
        "transition": "none",
        "subtitles": False,    # tắt sub để test đơn giản
        "voice_volume": 1.0,
        "bg_volume": 0.0,
        "ken_burns": False,
        "input_dir": DATA_DIR,   # M10: truyền data_dir làm input_dir (chứa srt + bg)
        "image_mode": "srt",
        "max_scenes": 3,
    }

    print("=" * 60)
    print("E2E RENDER TEST")
    print(f"  SRT    : {SRT_FILE}")
    print(f"  BG     : {BG_FILE}")
    print(f"  OUTPUT : {OUTPUT}")
    print(f"  CFG    : {cfg}")
    print("=" * 60)

    t0 = time.time()
    from services.render_service import render_video
    try:
        ok = render_video(
            SRT_FILE,
            DATA_DIR,
            OUTPUT,
            cfg=cfg,
            progress_cb=lambda m: print(f"  > {m}"),
        )
    except SystemExit as e:
        # ffmpeg / srt / audio thiếu → SystemExit. Coi là FAIL rõ ràng.
        raise AssertionError(f"render_video raised SystemExit: {e}")
    except Exception as e:
        raise AssertionError(f"render_video raised exception: {type(e).__name__}: {e}")
    elapsed = time.time() - t0

    assert ok is True, f"render_video returned {ok}"
    assert os.path.isfile(OUTPUT), f"FFmpeg Render Fail - File not created: {OUTPUT}"
    size = os.path.getsize(OUTPUT)
    assert size > 1024, f"Output too small ({size}B) — may be empty"
    print(f"\n✅ E2E Render OK: {OUTPUT} ({size:,} bytes, {elapsed:.1f}s)")
    return size, elapsed


if __name__ == "__main__":
    size, elapsed = test_full_render()
    print(f"\nFinal: {size:,} bytes in {elapsed:.1f}s")