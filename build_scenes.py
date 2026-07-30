#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py — Gom SRT (nhiều đoạn vụn) thành các CẢNH có timestamp.

Mục đích: tạo "xương sống thời gian" để mỗi prompt/ảnh gắn cứng vào một mốc
[start - end] lấy từ voiceover -> ảnh khớp lời cả NỘI DUNG lẫn THỜI GIAN.

Xuất ra scenes.csv với các cột:
    scene | start | end | dur | text(lời trong cảnh) | prompt(để trống cho Boss/AI điền)

Cách chạy:
    python build_scenes.py                       # gom mỗi cảnh ~8 giây
    python build_scenes.py --target 6            # mỗi cảnh ~6 giây (nhiều ảnh hơn)
    python build_scenes.py --srt input/subtitle.srt --out scenes.csv
"""
import argparse
import csv
import os

# Milestone 1 refactor — dùng group_scenes + nearest_veo từ domain.timeline.
from domain.timeline import group_scenes, nearest_veo_duration, fmt_clock
import auto_edit as ae   # vẫn dùng ae.parse_srt để CLI cũ chạy được

VEO_LEVELS = [4, 6, 8, 10]   # các mức độ dài clip Veo chọn được


# (group_scenes, nearest_veo_duration, fmt_clock đã import từ domain.timeline ở phần head)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--srt", default="input/subtitle.srt")
    ap.add_argument("--target", type=float, default=8.0, help="thời lượng mỗi cảnh (giây)")
    ap.add_argument("--out", default="scenes.csv")
    args = ap.parse_args()

    segs = ae.parse_srt(args.srt)
    scenes = group_scenes(segs, args.target)

    rows = []
    for i, sc in enumerate(scenes, 1):
        text = " ".join(t.strip() for t in sc["texts"]).strip()
        dur = round(sc["end"] - sc["start"], 2)
        veo, pct, speed_txt = nearest_veo_duration(dur, VEO_LEVELS)
        rows.append({
            "scene": i,
            "start": fmt_clock(sc["start"]),
            "end": fmt_clock(sc["end"]),
            "dur": dur,
            "veo_sec": veo,           # mức Veo nên tạo cho cảnh này
            "speed": speed_txt,       # tool sẽ đổi tốc độ chừng này để khít
            "text": text,
            "prompt": "",             # để trống cho Boss/AI điền prompt khớp lời
        })

    fields = ["scene", "start", "end", "dur", "veo_sec", "speed", "text", "prompt"]
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    total = scenes[-1]["end"] - scenes[0]["start"]
    clip_rows = [r for r in rows if isinstance(r["veo_sec"], int)]
    static_n = len(rows) - len(clip_rows)
    print(f"• {len(segs)} đoạn SRT  ->  {len(rows)} CẢNH (mỗi cảnh ~{args.target:g}s) "
          f"| tổng {total:.1f}s")
    print(f"• Đã ghi: {os.path.abspath(args.out)}")
    if clip_rows:
        pcts = [abs((r["dur"] / r["veo_sec"] - 1) * 100) for r in clip_rows]
        within15 = sum(1 for p in pcts if p <= 15)
        print(f"• Đổi tốc độ (clip Veo): TB {sum(pcts)/len(pcts):.1f}% | "
              f"cao nhất {max(pcts):.1f}% | "
              f"{within15}/{len(clip_rows)} cảnh dưới 15% (gần như vô hình)")
    if static_n:
        print(f"• {static_n} cảnh > {VEO_LEVELS[-1]}s -> ẢNH TĨNH "
              f"(Ken Burns kéo đủ giờ, không cần clip Veo)")
    print("\n--- 8 cảnh đầu ---")
    for r in rows[:8]:
        veo_disp = (f"Veo {r['veo_sec']}s ({r['speed']})"
                    if isinstance(r["veo_sec"], int) else r["speed"])
        print(f"  Cảnh {r['scene']:>2} | {r['dur']:>6}s → {veo_disp:>16} | {r['text'][:45]}")


if __name__ == "__main__":
    main()
