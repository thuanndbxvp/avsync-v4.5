"""Generate dummy fixtures for E2E render test.

Tạo:
  - tests/e2e/data/dummy.srt (4 sub segments, ~3s total)
  - tests/e2e/data/bg.jpg (solid color 320x240 JPEG via PIL nếu có, fallback raw)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def write_srt():
    srt_path = os.path.join(DATA_DIR, "dummy.srt")
    content = (
        "1\n00:00:00,000 --> 00:00:02,000\nHello E2E\n\n"
        "2\n00:00:02,000 --> 00:00:04,500\nRender test works\n\n"
        "3\n00:00:04,500 --> 00:00:07,000\nEnd of fixture\n\n"
    )
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(content)
    return srt_path


def write_bg():
    """Tạo 1 ảnh JPEG nhỏ 320x240 màu xám. Dùng PIL nếu có, fallback dùng ffmpeg."""
    bg_path = os.path.join(DATA_DIR, "bg.jpg")
    if os.path.isfile(bg_path) and os.path.getsize(bg_path) > 100:
        return bg_path
    try:
        from PIL import Image
        img = Image.new("RGB", (320, 240), color=(64, 96, 128))
        img.save(bg_path, "JPEG", quality=80)
        return bg_path
    except ImportError:
        pass
    # Fallback: dùng ffmpeg tạo 1 frame JPEG từ sourcesrc color filter
    import subprocess
    r = subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1",
         "-frames:v", "1", "-q:v", "5", bg_path],
        capture_output=True, timeout=10,
    )
    if not os.path.isfile(bg_path) or os.path.getsize(bg_path) < 100:
        raise RuntimeError(f"Không tạo được bg.jpg: {r.stderr.decode('utf-8', errors='ignore')[:200]}")
    return bg_path


if __name__ == "__main__":
    srt = write_srt()
    bg = write_bg()
    print(f"SRT: {srt} ({os.path.getsize(srt)} bytes)")
    print(f"BG : {bg} ({os.path.getsize(bg)} bytes)")
    print("Fixtures OK.")