"""Smoke test Milestone 1 refactor: domain + infrastructure + backward-compat."""
import sys
sys.path.insert(0, r"d:\auto-edit-video-main")

# Test 1: domain imports pure
from domain.timeline import (
    parse_srt, srt_time_to_sec, ass_time, hex_to_ass,
    group_scenes, split_word_times, fmt_clock, nearest_veo_duration,
)
from domain.visual_style import (
    as_json, style_caption, style_caption_is_empty, style_for_ai,
    strip_mode_keys, scene_mode_keys, character_keys, to_text, deep_collect,
)
from infrastructure.filesystem import natural_key, collect_media, app_dir
from infrastructure.shell_runner import run_cmd, quote_for_log
print("[OK] domain + infrastructure imports clean")

# Test 2: backward-compat qua auto_edit / ai_prompts
import auto_edit as ae
import ai_prompts as ap
assert callable(ae.parse_srt), "ae.parse_srt missing"
assert callable(ae._ass_time), "ae._ass_time missing"
assert callable(ae._hex_to_ass), "ae._hex_to_ass missing"
assert callable(ae._split_word_times), "ae._split_word_times missing"
assert callable(ae.collect_media), "ae.collect_media missing"
assert callable(ae.find_voice), "ae.find_voice missing"
assert callable(ae.find_tool), "ae.find_tool missing"
print("[OK] auto_edit backward-compat (parse_srt, _ass_time, _hex_to_ass, _split_word_times, collect_media, find_voice, find_tool)")

assert callable(ap._style_caption), "ap._style_caption missing"
assert callable(ap._style_for_ai), "ap._style_for_ai missing"
assert callable(ap._as_json), "ap._as_json missing"
assert callable(ap._scene_mode_keys), "ap._scene_mode_keys missing"
assert callable(ap._character_keys), "ap._character_keys missing"
assert callable(ap._strip_mode_keys), "ap._strip_mode_keys missing"
assert callable(ap.style_caption_is_empty), "ap.style_caption_is_empty missing"
print("[OK] ai_prompts backward-compat (_style_caption, _style_for_ai, _as_json, ...)")

# Test 3: pure behavior
assert srt_time_to_sec("00:00:01,500") == 1.5
assert srt_time_to_sec("01:02:03.250") == 3723.25
assert ass_time(0) == "0:00:00.00"
assert ass_time(65.5) == "0:01:05.50"
assert hex_to_ass("#FF0000") == "&H000000FF"
assert hex_to_ass("#00FF00") == "&H0000FF00"
print("[OK] domain.timeline pure functions")

# Test 4: style caption
style_json = '{"art_style": "cinematic ink", "characters": {"modern_human": "..."}, "scene_modes": {"ancient_day": "..."}}'
cap = ap._style_caption(style_json)
cap_lower = cap.lower()
assert "cinematic ink" in cap_lower, f"Expected cinematic ink in: {cap}"
ai_style = ap._style_for_ai(style_json)
assert "cinematic" not in ai_style, f"AI style should NOT contain art fields: {ai_style}"
assert "scene_modes" in ai_style or "characters" in ai_style
print("[OK] domain.visual_style caption + AI split")

# Test 5: parse_srt_from_text
srt_text = "1\n00:00:01,000 --> 00:00:03,500\nHello world\n\n2\n00:00:04,000 --> 00:00:07,000\nSecond scene\n"
segs = ae.parse_srt_from_text(srt_text)
assert len(segs) == 2
assert segs[0]["text"] == "Hello world"
assert segs[1]["start"] == 4.0
print("[OK] parse_srt_from_text")

# Test 6: group_scenes
scenes = group_scenes(segs, target=10.0)
assert len(scenes) == 1
print("[OK] group_scenes")

# Test 7: collect_media (raise SystemExit khi folder không tồn tại)
try:
    ae.collect_media(r"D:\nonexistent_xyz")
    raise AssertionError("Expected SystemExit")
except SystemExit as e:
    pass
print("[OK] collect_media SystemExit on missing dir")

# Test 8: nearest_veo (8 là gần 7 nhất với target=7.5)
level, pct, txt = nearest_veo_duration(7.5, [4, 6, 8, 10])
assert level == 8, f"Expected 8 (closest to 7.5), got {level}"
# Cảnh quá dài -> ảnh tĩnh
level, pct, txt = nearest_veo_duration(15.0, [4, 6, 8, 10])
assert level == "tĩnh", f"Expected 'tĩnh' for >10.5s, got {level}"
print("[OK] nearest_veo_duration")

# Test 9: workers vẫn import được
import sys
sys.path.insert(0, r"d:\auto-edit-video-main")
import core.worker_render as wr
import core.worker_prompt as wp
import core.worker_sleep as ws
import core.worker_queue as wq
print("[OK] core.worker_* imports (render, prompt, sleep, queue)")

# Test 10: UI imports
import ui.main_window as mw
import ui.tabs.tab_prompt as tp
print("[OK] ui.main_window + ui.tabs.tab_prompt")

print("\n=== ALL MILESTONE 1 TESTS PASSED ===")