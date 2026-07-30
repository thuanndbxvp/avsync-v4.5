"""domain.timeline — Time / SRT / subtitle helpers (pure, no I/O).

Di chuyển từ `auto_edit.py` và `build_scenes.py` (Milestone 1 refactor).
Mọi hàm ở đây chỉ nhận input và trả output — KHÔNG đọc file, KHÔNG gọi shell.
"""
from __future__ import annotations

import re
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Time conversions (giây <-> string)
# ---------------------------------------------------------------------------
def srt_time_to_sec(t: str) -> float:
    """'00:00:01,500' hoặc '00:00:01.500' -> 1.5"""
    h, m, rest = t.split(":")
    s, ms = rest.replace(".", ",").split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def ass_time(t: float) -> str:
    """giây -> 'H:MM:SS.cc' (centisecond) cho file ASS."""
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return (
        f"{h}:{m:02d}:{int(s):02d}."
        f"{int(round((s - int(s)) * 100)):02d}"
    )


def fmt_clock(t: float) -> str:
    """giây -> 'HH:MM:SS,mmm' (cho CSV / log)."""
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---------------------------------------------------------------------------
# Color / ASS helpers (pure)
# ---------------------------------------------------------------------------
def hex_to_ass(hexcol: str, default: str = "&H0000FFFF") -> str:
    """'#RRGGBB' -> ASS '&H00BBGGRR' (ASS dùng BGR). Lỗi -> vàng mặc định."""
    try:
        h = str(hexcol).lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
    except Exception:
        return default


# ---------------------------------------------------------------------------
# SRT parsing (pure — chỉ nhận path, dùng open() là I/O, nhưng tách riêng
# parse_srt_from_text để dễ test không cần file thật)
# ---------------------------------------------------------------------------
_TIME_RE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)


def parse_srt_from_text(raw: str) -> list[dict]:
    """Parse text SRT thành list[{'start','end','text'}] đã sort theo start."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n\s*\n", raw)
    segs: list[dict] = []
    for b in blocks:
        m = _TIME_RE.search(b)
        if not m:
            continue
        lines = b.split("\n")
        # bỏ dòng timestamp + dòng số thứ tự -> còn lại là text
        text_lines = [
            ln for ln in lines
            if not _TIME_RE.search(ln) and not ln.strip().isdigit()
        ]
        text = " ".join(ln.strip() for ln in text_lines).strip()
        segs.append({
            "start": srt_time_to_sec(m.group(1)),
            "end": srt_time_to_sec(m.group(2)),
            "text": text,
        })
    segs.sort(key=lambda s: s["start"])
    return segs


def parse_srt(path: str) -> list[dict]:
    """Đọc file SRT rồi parse. Wrapper có I/O — nhưng logic parse thuần."""
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()
    return parse_srt_from_text(raw)


# ---------------------------------------------------------------------------
# Word timing (chia đều duration theo tỉ lệ số ký tự)
# ---------------------------------------------------------------------------
def split_word_times(seg: dict, uppercase: bool = False) -> list[tuple[str, float, float]]:
    """Trả [(word, start, end), ...] cho 1 đoạn SRT.

    Chia thời lượng câu theo TỈ LỆ SỐ KÝ TỰ (SRT chỉ có mốc theo câu -> từ dài
    giữ lâu hơn, gần khớp giọng). Từ cuối kéo tới hết câu -> các từ nối liền mạch.
    """
    words = " ".join(seg["text"].split()).split(" ")
    if uppercase:
        words = [w.upper() for w in words]
    weights = [max(1, len(w)) for w in words]
    tw = sum(weights) or 1
    total = max(0.0, seg["end"] - seg["start"])
    out: list[tuple[str, float, float]] = []
    t = seg["start"]
    for i, w in enumerate(words):
        if i < len(words) - 1:
            d = total * weights[i] / tw
        else:
            d = max(0.01, seg["end"] - t)
        out.append((w, t, t + d))
        t += d
    return out


# ---------------------------------------------------------------------------
# Scene grouping (gom các segment SRT thành các cảnh ~target giây)
# ---------------------------------------------------------------------------
# Các dấu ngắt câu hợp lệ — khi câu hiện tại kết thúc bằng 1 trong các dấu này
# thì ĐƯỢC phép chốt cảnh (dù đang vượt target). Đảm bảo "không mất chữ".
END_PUNCTUATION = (".", "?", "!", "...", "”", '"')
# Hard limit: nếu câu vượt target + 5s mà vẫn chưa có dấu ngắt, chốt khẩn cấp
# để cảnh không lê thê (tránh treo AI / clip Veo quá dài).
HARD_LIMIT_PAD = 5.0


def _ends_with_punctuation(text: str) -> bool:
    """True nếu text kết thúc bằng dấu ngắt câu (., ?, !, ..., ”, ").

    Lưu ý: check '...' TRƯỚC, sau đó mới check '.' đơn lẻ (endswith ưu tiên match
    dài hơn khi dùng tuple, nhưng an toàn hơn với logic tách).
    """
    s = text.strip()
    if not s:
        return False
    if s.endswith("..."):
        return True
    return s[-1] in END_PUNCTUATION


def group_scenes(
    segs: Sequence[dict],
    target: float,
    *,
    hard_limit_pad: float = HARD_LIMIT_PAD,
) -> list[dict]:
    """Gom các đoạn SRT thành cảnh với hybrid Time-based + Semantic-based split.

    Time-based (cũ): gom các đoạn liền nhau cho tới khi đạt ~target giây.
    Semantic-based (M1.5): khi đạt target, CHỈ chốt cảnh nếu câu hiện tại đã kết
    thúc bằng dấu ngắt câu (., ?, !, ..., ”, ") — đảm bảo KHÔNG mất chữ.
    Nếu câu CHƯA kết thúc, vượt target để gộp tiếp — trừ khi vượt hard limit
    (target + hard_limit_pad) thì chốt khẩn cấp.

    Trả list[{start,end,texts}] với 'texts' = list câu thoại trong cảnh.
    Cảnh cuối cùng: end = start của cảnh kế (nối liền mạch).
    """
    hard_limit = target + hard_limit_pad
    scenes: list[dict] = []
    cur: dict | None = None
    for s in segs:
        if cur is None:
            cur = {"start": s["start"], "end": s["end"], "texts": [s["text"]]}
            continue
        duration_if_added = s["end"] - cur["start"]
        if duration_if_added >= target:
            # Đạt target — kiểm tra semantic
            if _ends_with_punctuation(s["text"]) or duration_if_added > hard_limit:
                # Câu đã tròn HOẶC vượt hard limit -> chốt cảnh rồi reset cur
                cur["end"] = s["end"]
                cur["texts"].append(s["text"])
                scenes.append(cur)
                cur = None   # vòng sau sẽ khởi tạo cur từ segment kế
                continue
        # Chưa tới target HOẶC đã tới target nhưng câu chưa tròn + chưa vượt hard limit
        cur["end"] = s["end"]
        cur["texts"].append(s["text"])
    if cur:
        scenes.append(cur)
    # nối liền mạch
    for i in range(len(scenes) - 1):
        scenes[i]["end"] = scenes[i + 1]["start"]
    return scenes


# ---------------------------------------------------------------------------
# Scene flattener (gộp text trong cảnh)
# ---------------------------------------------------------------------------
def flatten_scene_text(scene: dict) -> str:
    """Nối các câu thoại trong 1 cảnh thành 1 chuỗi (dọn khoảng trắng thừa)."""
    return " ".join(t.strip() for t in scene["texts"]).strip()


def nearest_veo_duration(dur: float, veo_levels: Iterable[int]) -> tuple:
    """Chọn mức Veo gần nhất + % phải đổi tốc độ để khít cảnh.

    dur > max(veo_levels)+0.5 -> ('tĩnh', 0.0, 'ẢNH TĨNH') — cảnh quá dài.
    Ngược lại trả (level, pct, txt) trong đó pct > 0 = chậm lại, < 0 = nhanh lên.
    """
    levels = list(veo_levels)
    if not levels:
        return "tĩnh", 0.0, "ẢNH TĨNH"
    if dur > levels[-1] + 0.5:
        return "tĩnh", 0.0, "ẢNH TĨNH"
    level = min(levels, key=lambda L: abs(L - dur))
    pct = (dur / level - 1) * 100
    if abs(pct) < 1:
        txt = "khít"
    else:
        txt = f"{abs(pct):.0f}% {'chậm' if pct > 0 else 'nhanh'}"
    return level, pct, txt