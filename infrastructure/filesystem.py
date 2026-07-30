"""infrastructure.filesystem — I/O liên quan đến file/thư mục.

Bọc `os.listdir`, scan media, tìm file theo pattern. Tách khỏi `auto_edit.py`
để dễ test + dễ thay thế bằng async wrapper sau.
"""
from __future__ import annotations

import os
import re
from typing import Iterable, Optional, Sequence


# Extensions mặc định — auto_edit giữ nguyên constant IMG_EXTS/VIDEO_EXTS/AUDIO_NAMES.
DEFAULT_IMAGE_EXTS: tuple[str, ...] = (
    ".png", ".jpg", ".jpeg", ".webp", ".bmp",
)
DEFAULT_VIDEO_EXTS: tuple[str, ...] = (
    ".mp4", ".mov", ".mkv", ".webm",
)
DEFAULT_AUDIO_NAMES: tuple[str, ...] = (
    "voice.mp3", "voice.wav", "voice.m4a",
    "voiceover.mp3", "voiceover.wav",
)


def natural_key(s: str) -> list:
    """Sort key tự nhiên: file_2 < file_10 (tách số ra so sánh riêng)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def collect_media(
    folder: str,
    image_exts: Optional[Sequence[str]] = None,
    video_exts: Optional[Sequence[str]] = None,
) -> list[str]:
    """Liệt kê file ảnh/video trong thư mục, sort tự nhiên.

    Raises SystemExit nếu thư mục không tồn tại (giữ compat với code cũ).
    """
    if not os.path.isdir(folder):
        raise SystemExit(f"Không thấy thư mục ảnh: {folder}")
    ie = tuple(image_exts) if image_exts is not None else DEFAULT_IMAGE_EXTS
    ve = tuple(video_exts) if video_exts is not None else DEFAULT_VIDEO_EXTS
    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith(ie + ve)
    ]
    files.sort(key=natural_key)
    return [os.path.join(folder, f) for f in files]


def find_voice(
    input_dir: str,
    explicit: Optional[str] = None,
    audio_names: Optional[Iterable[str]] = None,
) -> Optional[str]:
    """Tìm file voice: ưu tiên đường dẫn explicit, nếu không thì dò theo tên mặc định.

    Trả None nếu không tìm thấy.
    """
    if explicit:
        if not os.path.isfile(explicit):
            raise SystemExit(f"Không thấy file voice: {explicit}")
        return explicit
    names = tuple(audio_names) if audio_names is not None else DEFAULT_AUDIO_NAMES
    for name in names:
        p = os.path.join(input_dir, name)
        if os.path.isfile(p):
            return p
    return None


def app_dir() -> str:
    """Thư mục chứa .exe (Nuitka/PyInstaller) hoặc script (dev)."""
    import sys
    if getattr(sys, "frozen", False) or ("__compiled__" in globals()):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))