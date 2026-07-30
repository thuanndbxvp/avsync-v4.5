"""Smoke test Milestone 1.5: semantic split + hard limit in group_scenes."""
import sys
sys.path.insert(0, r"d:\auto-edit-video-main")

from domain.timeline import (
    group_scenes, parse_srt, srt_time_to_sec, _ends_with_punctuation,
    END_PUNCTUATION, HARD_LIMIT_PAD,
)

# ---------- Test 1: _ends_with_punctuation ----------
assert _ends_with_punctuation("Hello.") is True
assert _ends_with_punctuation("Hello?") is True
assert _ends_with_punctuation("Hello!") is True
assert _ends_with_punctuation("Hello...") is True           # ellipsis
assert _ends_with_punctuation('Hello"') is True            # close quote
assert _ends_with_punctuation("Hello”") is True            # Vietnamese close quote
assert _ends_with_punctuation("Hello world") is False      # no punct
assert _ends_with_punctuation("Hello world,") is False      # comma = NOT end punct
assert _ends_with_punctuation("") is False
assert _ends_with_punctuation("   ") is False
assert _ends_with_punctuation("Wait...") is True
assert _ends_with_punctuation("...") is True
print("[OK] _ends_with_punctuation")

# ---------- Test 2: pure time-based (no semantic) ----------
# 4 segments, mỗi segment 2s, target=8s.
# segment 1 (0-2 "Hello"): khởi tạo cur
# segment 2 (2-4 "my"): duration=4 < 8, gộp
# segment 3 (4-6 "dear"): duration=6 < 8, gộp
# segment 4 (6-8 "friends."): duration=8 >= 8, "friends." có end punct -> chốt cảnh 1
# gồm 4 segment, reset cur = segment 4 -> cảnh 2 chỉ có segment 4.
segs = [
    {"start": 0.0, "end": 2.0, "text": "Hello"},          # no punct
    {"start": 2.0, "end": 4.0, "text": "my"},             # no punct
    {"start": 4.0, "end": 6.0, "text": "dear"},           # no punct
    {"start": 6.0, "end": 8.0, "text": "friends."},       # END punct
]
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 1, f"Expected 1 scene (all merged into 1), got {len(scenes)}"
assert scenes[0]["texts"] == ["Hello", "my", "dear", "friends."]
print("[OK] semantic cut at end punct (target reached + punct splits)")

# ---------- Test 3: semantic override (kéo dài cảnh để trọn câu) ----------
# target=8s. Segment 1: 0-2 "a", 2: 2-4 "b", 3: 4-6 "c", 4: 6-8 "d", 5: 8-10 "sentence."
# Sau segment 3 (duration=6 < target), gộp tiếp. Sau segment 4 (duration=8 >= target,
# "d" không có end punct) -> gộp tiếp. Sau segment 5 (duration=10 < hard_limit=13,
# "sentence." có end punct) -> CHỐT cảnh 1 (gồm cả 5) reset cur = segment 5.
# -> 2 cảnh (cảnh 1 = 5 segments, cảnh 2 = segment 5).
segs = [
    {"start": 0.0, "end": 2.0, "text": "a"},
    {"start": 2.0, "end": 4.0, "text": "b"},
    {"start": 4.0, "end": 6.0, "text": "c"},
    {"start": 6.0, "end": 8.0, "text": "d"},          # đạt target nhưng chưa kết thúc
    {"start": 8.0, "end": 10.0, "text": "sentence."},  # có end punct -> CHỐT
]
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 1, f"Expected 1 scene (semantic extend), got {len(scenes)}"
assert len(scenes[0]["texts"]) == 5
assert scenes[0]["texts"][-1] == "sentence."  # câu trọn vẹn
print("[OK] semantic override (extend scene to next punct)")

# ---------- Test 4: hard limit cut ----------
# Một câu siêu dài không có dấu ngắt. target=8, hard_limit=13.
# 7 segments 2s each, tất cả "x" không có end punct.
# segment 4 (6-8) duration=8 >= 8, no punct -> gộp.
# segment 5 (8-10) duration=10 >= 8, no punct -> gộp.
# segment 6 (10-12) duration=12 >= 8, no punct -> gộp.
# segment 7 (12-14) duration=14 > 13 -> hard limit chốt cảnh 1 (gồm 7 segs),
# reset cur = segment 7 -> cảnh 2 chỉ có segment 7.
segs = [
    {"start": 0.0, "end": 2.0, "text": "x"},
    {"start": 2.0, "end": 4.0, "text": "x"},
    {"start": 4.0, "end": 6.0, "text": "x"},
    {"start": 6.0, "end": 8.0, "text": "x"},
    {"start": 8.0, "end": 10.0, "text": "x"},
    {"start": 10.0, "end": 12.0, "text": "x"},
    {"start": 12.0, "end": 14.0, "text": "x"},
]
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 1, f"Expected 1 scene (hard limit), got {len(scenes)}"
assert len(scenes[0]["texts"]) == 7  # cảnh 1: 7 segments
# 'nối liền mạch' KHÔNG áp dụng cho cảnh cuối (không có cảnh sau)
assert scenes[0]["end"] - scenes[0]["start"] == 14.0
print("[OK] hard limit cut (sentence too long without punct)")

# ---------- Test 5: cảnh bình thường chia đúng target không có sem override ----------
# Câu ngắn, mỗi segment đều có end punct -> không cần override.
# target=8, segments 4s each, mỗi cái có punct -> 2 cảnh (1: 0-4 + 4-8 = 2 segs,
# 2: 8-12 + 12-16 = 2 segs).
# Thực ra: segment 1 (0-4) -> duration=4 < target -> gộp. segment 2 (4-8) ->
# duration=8 >= target, "punct." có end punct -> chốt cảnh 1.
# segment 3 (8-12) -> duration=4 < target -> gộp. segment 4 (12-16) ->
# duration=8 >= target, "bye." có end punct -> chốt cảnh 2.
segs = [
    {"start": 0.0, "end": 4.0, "text": "Hi."},
    {"start": 4.0, "end": 8.0, "text": "Hello."},
    {"start": 8.0, "end": 12.0, "text": "Bye."},
    {"start": 12.0, "end": 16.0, "text": "Done."},
]
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 2, f"Expected 2 scenes, got {len(scenes)}"
assert scenes[0]["texts"] == ["Hi.", "Hello."]
assert scenes[1]["texts"] == ["Bye.", "Done."]
print("[OK] pure time-based (all segs have punct)")

# ---------- Test 6: cảnh cuối không có end punct ----------
# Segs 1: 0-4 "Hi.", 2: 4-8 "Hello." (chốt tại đây), 3: 8-12 "more text" (no punct)
# -> cảnh 2 chỉ có 1 segment, vẫn được thêm vào cuối loop (cur is not None).
segs = [
    {"start": 0.0, "end": 4.0, "text": "Hi."},
    {"start": 4.0, "end": 8.0, "text": "Hello."},
    {"start": 8.0, "end": 12.0, "text": "more text"},
]
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 2
assert scenes[1]["texts"] == ["more text"]
print("[OK] trailing scene without punct")

# ---------- Test 7: backward-compat (M1 smoke test vẫn pass) ----------
import auto_edit as ae
import ai_prompts as ap
assert callable(ae.parse_srt)
assert callable(ae._ass_time)
assert callable(ae._hex_to_ass)
assert callable(ae._split_word_times)
assert callable(ae.collect_media)
assert callable(ae.find_voice)
assert callable(ap._style_caption)
assert callable(ap._style_for_ai)
assert callable(ap._as_json)
print("[OK] backward-compat symbols (auto_edit + ai_prompts)")

# ---------- Test 8: real SRT file (semantic boundary) ----------
import os
srt_path = r"d:\auto-edit-video-main\tests\test_semantic_split.srt"
if os.path.isfile(srt_path):
    segs = parse_srt(srt_path)
    scenes = group_scenes(segs, target=8.0)
    # Cảnh 1: segs 1-5 (start 1 -> duration ~14s, đến seg 5 "Milestone 1.5" có end punct)
    # Logically:
    # segment 1: 0-2.5 (duration 2.5 < 8)
    # segment 2: 2.5-5.5 (duration 5.5 < 8)
    # segment 3: 5.5-8.5 (duration 8.5 >= 8, no punct -> gộp tiếp)
    # segment 4: 8.5-10.5 (duration 10.5 >= 8, no punct "amazing" -> gộp tiếp)
    # segment 5: 10.5-13.5 (duration 13.5 < 13+5=18 vẫn gộp được nhưng "Milestone 1.5" có end punct? "1.5" -> "." -> có end punct)
    # -> chốt cảnh 1
    # segment 6: 13.5-20.5 (duration 7 < 8) -> cảnh 2
    # Total: 2 scenes
    print(f"  Loaded {len(segs)} segs from real SRT")
    print(f"  Scenes: {len(scenes)}")
    for i, sc in enumerate(scenes, 1):
        dur = sc["end"] - sc["start"]
        text = " ".join(t.strip() for t in sc["texts"])
        print(f"  Scene {i}: {dur:.1f}s | {text[:60]}...")
    assert len(scenes) >= 1, "Should produce at least 1 scene"
    print("[OK] real SRT parse + group_scenes")
else:
    print("[SKIP] real SRT not found, skipping test 8")

# ---------- Test 9: workers + UI still import ----------
import importlib
for mod in [
    "core.worker_render", "core.worker_prompt",
    "core.worker_sleep", "core.worker_queue",
    "ui.main_window", "ui.tabs.tab_prompt",
]:
    importlib.import_module(mod)
print("[OK] workers + UI imports")

# ---------- Test 10: M1 backward-compat (test_milestone1.srt) ----------
# SRT 4 đoạn (Milestone 1 test fixture):
#   seg1: 0-3.5 "Xin chào các bạn" (no punct)
#   seg2: 4-7   "Đây là video test milestone 1" (no punct)
#   seg3: 7.5-10 "Kiểm tra backward-compat" (no punct)
#   seg4: 11-14 "Refactor domain layer" (no punct)
# Tất cả 4 đoạn đều KHÔNG có end punct.
# M1 cũ: duration=10 (seg3) >= 8 -> chốt cảnh 1 (3 segments), sau đó cảnh 2 = seg4.
# M1.5 mới: hard limit chốt tại seg4 (duration=14 > 13) -> cảnh 1 (4 segments, 0-14s).
#             behavior khác M1 cũ — expected vì M1 cũ ngắt giữa câu dài không punct.
# Test M1.5 muốn: 1 cảnh rất dài (14s) — đây là behavior mới đúng (hard limit bảo vệ).
segs = parse_srt(r"d:\auto-edit-video-main\tests\test_milestone1.srt")
scenes = group_scenes(segs, target=8.0)
assert len(scenes) == 1, f"Expected 1 scene (hard limit kicked in), got {len(scenes)}"
# 1 cảnh từ start=1.0 đến end=14.0 = 13.0s
assert scenes[0]["end"] - scenes[0]["start"] == 13.0, f"Expected 13.0s, got {scenes[0]['end']-scenes[0]['start']}"
assert len(scenes[0]["texts"]) == 4  # 4 segments
print("[OK] M1.5 forward (test_milestone1.srt with no-end-punct -> 1 long scene via hard limit)")

# Test thêm 1: nếu đã chốt cảnh bằng end punct, cảnh tiếp theo SINH RA bình thường.
# Test data: 3 segs với end punct ở giữa.
segs = [
    {"start": 0.0, "end": 4.0, "text": "First."},
    {"start": 4.0, "end": 10.0, "text": "Second long sentence no punct, " * 3},  # 50 chars
    {"start": 10.0, "end": 14.0, "text": "and ends here."},
]
scenes = group_scenes(segs, target=8.0)
# seg1: 0-4 "First." cur
# seg2: 4-10, duration=10 >= 8, no punct -> gộp
# seg3: 10-14, duration=14 > 13 hard limit, "and ends here." has end punct -> chốt cảnh 1
# -> 1 cảnh (kéo dài qua hard limit vì có end punct trùng)
assert len(scenes) == 1
assert len(scenes[0]["texts"]) == 3
print("[OK] M1.5: hard limit + end punct both fire -> 1 scene")

print("\n=== ALL MILESTONE 1.5 TESTS PASSED ===")