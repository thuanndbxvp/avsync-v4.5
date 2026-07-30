"""domain.render_plan — Render Plan logic (pure, no I/O).

Di chuyển logic planning (chọn cảnh, tính duration, chọn FPS, chọn encoder)
từ `auto_edit.render_video()` 400 dòng. Tách THÀNH 2 PHẦN:
  1. Pure plan (input -> dataclass) — không đụng ffmpeg/file
  2. Build master clip (dataclass -> ffmpeg cmd) — thuộc infrastructure

Mục tiêu M3: cho phép test toàn bộ logic planning (chọn scenes từ nhiều mode,
auto fps, encoder, max_scenes, dry_run, ...) mà KHÔNG cần ffmpeg thật.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence


# Cấu hình ảnh/video/audio — phải khớp auto_edit_mợi
DEFAULT_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
DEFAULT_VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm")
DEFAULT_AUDIO_NAMES = ("voice.mp3", "voice.wav", "voice.m4a",
                       "voiceover.mp3", "voiceover.wav")


@dataclass
class ScenePlan:
    """1 cảnh trong plan: (source_path, duration_seconds)."""
    source: str        # đường dẫn ảnh hoặc clip
    duration: float    # giây

    @property
    def is_image(self) -> bool:
        return self.source.lower().endswith(DEFAULT_IMAGE_EXTS)

    @property
    def is_video(self) -> bool:
        return self.source.lower().endswith(DEFAULT_VIDEO_EXTS)


@dataclass
class RenderPlan:
    """Kế hoạch render ĐẦY ĐỦ — pure data, không có side-effect."""
    scenes: list[ScenePlan] = field(default_factory=list)
    total_duration: float = 0.0
    fps: int = 30
    fps_reason: str = "default"
    encoder: str = "libx264"
    jobs: int = 1
    aspect: str = "16:9"
    width: int = 1920
    height: int = 1080
    mode: str = "auto"            # "auto" | "spread" | "srt" | "scenes"
    mode_label: str = ""
    audio_dur: Optional[float] = None
    voice_path: Optional[str] = None
    bgm_path: Optional[str] = None
    sfx_path: Optional[str] = None
    logo_path: Optional[str] = None
    keep_clip_audio: bool = False
    keep_temp: bool = False
    no_kenburns: bool = False
    no_subtitles: bool = False
    no_duck: bool = False
    transition: str = "none"
    xfade_duration: float = 0.5
    color: str = "none"
    vignette: bool = False
    grain: bool = False
    title_text: Optional[str] = None
    title_sec: float = 4.0
    intro: Optional[str] = None
    outro: Optional[str] = None
    sub_font: Optional[str] = None
    sub_mode: str = "word"
    sub_outline_color: Optional[str] = None
    sub_size: int = 52
    karaoke_color: str = "#FFFF00"
    clip_fit: str = "auto"
    clip_volume: float = 0.25
    voice_volume: float = 1.0
    sfx_volume: float = 0.5
    bgm_volume: float = 0.18
    logo_pos: str = "br"
    logo_size: int = 96
    logo_opacity: float = 0.85
    logo_shape: str = "round"
    max_scenes: Optional[int] = None
    dry_run: bool = False

    @property
    def has_video(self) -> bool:
        return any(s.is_video for s in self.scenes)

    @property
    def has_audio_mix(self) -> bool:
        return bool(self.bgm_path or self.keep_clip_audio or self.sfx_path or self.logo_path)


# ---------------------------------------------------------------------------
# Planning helpers (pure)
# ---------------------------------------------------------------------------
def plan_scenes(
    *,
    segs: Sequence[dict],
    media: Sequence[str],
    total_end: float,
    mode: str,
    seconds_per_image: Optional[float] = None,
    scenes_csv: Optional[str] = None,
    n_img: Optional[int] = None,
    n_seg: Optional[int] = None,
    min_clip: float = 0.4,
) -> tuple[list[ScenePlan], str]:
    """Chọn cách rải ảnh -> list[ScenePlan] + mode_label.

    Trả về (scenes, mode_label). 4 mode:
      - scenes_csv (ưu tiên cao nhất): đọc file CSV {start, end} -> khóa timestamp
      - seconds_per_image: chia tổng thời gian / spi -> N cảnh bằng nhau
      - "srt": 1 ảnh / 1 đoạn phụ đề theo boundary của SRT
      - "spread": rải đều N ảnh full-time
    """
    n_img = n_img if n_img is not None else len(media)
    n_seg = n_seg if n_seg is not None else len(segs)

    # Auto-resolve mode
    if mode == "auto" and not seconds_per_image and not scenes_csv:
        mode = "srt" if n_img == n_seg else "spread"

    if scenes_csv:
        scenes: list[ScenePlan] = []
        with open(scenes_csv, encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f)):
                st = _srt_time_to_sec(row["start"])
                en = _srt_time_to_sec(row["end"])
                src = media[min(i, n_img - 1)] if n_img else ""
                scenes.append(ScenePlan(source=src, duration=max(min_clip, en - st)))
        mode_label = f"theo bảng cảnh ({len(scenes)} cảnh, khóa timestamp SRT)"
    elif seconds_per_image:
        n_scenes = max(1, round(total_end / seconds_per_image))
        scenes = []
        for i in range(n_scenes):
            d = seconds_per_image if i < n_scenes - 1 else \
                max(min_clip, total_end - seconds_per_image * (n_scenes - 1))
            scenes.append(ScenePlan(source=media[i % n_img] if n_img else "",
                                    duration=d))
        mode_label = f"mỗi ảnh ~{seconds_per_image:g}s (lặp vòng {n_img} ảnh)"
    elif mode == "srt":
        boundaries = [0.0] + [segs[i]["start"] for i in range(1, n_seg)] + [total_end]
        scenes = []
        for i in range(n_seg):
            src = media[min(i, n_img - 1)] if n_img else ""
            d = max(min_clip, boundaries[i + 1] - boundaries[i])
            scenes.append(ScenePlan(source=src, duration=d))
        mode_label = "1 ảnh / 1 đoạn phụ đề"
    else:  # spread
        per = total_end / max(n_img, 1)
        scenes = [ScenePlan(source=media[i], duration=per) for i in range(n_img)]
        mode_label = f"rải đều {n_img} ảnh"
    return scenes, mode_label


def choose_fps(
    scenes: Sequence[ScenePlan],
    requested_fps: Optional[int] = None,
    probed_fps: Optional[dict] = None,
) -> tuple[int, str]:
    """Chọn FPS: khớp clip Veo để HẾT RUNG.
    - explicit -> dùng
    - có video -> dùng fps của clip (probe trước)
    - toàn ảnh -> 30 (Ken Burns mượt)
    """
    if requested_fps:
        return max(1, int(requested_fps)), "theo --fps"
    has_video = any(s.is_video for s in scenes)
    if has_video:
        # Tìm video đầu tiên để probe FPS
        for s in scenes:
            if s.is_video and probed_fps and s.source in probed_fps:
                f = probed_fps[s.source]
                return int(round(f)) if f else 24, "khớp clip video -> hết rung"
        return 24, "khớp clip video -> hết rung (default)"
    return 30, "toàn ảnh tĩnh -> Ken Burns mượt"


def choose_encoder_jobs(
    encoder: str = "libx264",
    cpu_count: int = 4,
    requested_jobs: Optional[int] = None,
) -> tuple[str, int]:
    """Chọn encoder + số jobs = max(1, min(4, cpu//2)) cho CPU, cap 3 cho GPU."""
    enc = encoder or "libx264"
    cpu = max(1, cpu_count)
    auto_jobs = max(1, min(4, cpu // 2))
    if enc != "libx264":
        auto_jobs = min(auto_jobs, 3)
    jobs = requested_jobs if (requested_jobs and requested_jobs > 0) else auto_jobs
    return enc, jobs


def apply_max_scenes(
    scenes: list[ScenePlan], max_scenes: Optional[int], total_end: float,
) -> tuple[list[ScenePlan], float, str]:
    """Nếu max_scenes > 0 và scenes > max_scenes -> cắt + ghi lại total_end."""
    if max_scenes and max_scenes > 0 and len(scenes) > max_scenes:
        scenes = scenes[:max_scenes]
        total_end = sum(s.duration for s in scenes)
        return scenes, total_end, f"XEM TRƯỚC {len(scenes)} cảnh đầu"
    return scenes, total_end, ""


# ---------------------------------------------------------------------------
# Helpers (local copies — avoids circular import auto_edit)
# ---------------------------------------------------------------------------
def _srt_time_to_sec(t: str) -> float:
    """Pure: '00:00:01,500' -> 1.5."""
    h, m, rest = t.split(":")
    s, ms = rest.replace(".", ",").split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def derive_total_end(segs: Sequence[dict], audio_dur: Optional[float]) -> float:
    """Tổng thời lượng video = max(cuối SRT, audio_dur)."""
    if not segs:
        return 0.0
    end = segs[-1]["end"]
    if audio_dur:
        return max(end, audio_dur)
    return end


def normalize_aspect(aspect: str) -> tuple[int, int]:
    """Trả (width, height) theo aspect. 9:16 -> 1080x1920, mặc định 1920x1080."""
    if aspect == "9:16":
        return 1080, 1920
    return 1920, 1080