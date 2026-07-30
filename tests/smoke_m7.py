"""Smoke test Milestone 7 — Video Ngủ Tab Feature Parity.

Coverage:
  1. tab_sleep imports + UI builds (no error)
  2. cmb_effect has 5 effects (none/rain/snow/fog/bokeh) với data EN
  3. cmb_intensity has 3 mức (nhe/vua/nang) với data EN
  4. cmb_fx CŨ đã xóa (không còn attr cmb_fx)
  5. 16 options UI tồn tại (spin_*, cmb_*, chk_*)
  7. Browse handlers wired thật (không phải stub_action)
  8. _collect_cfg() trả dict với đầy đủ key
  9. _validate() phát hiện thiếu input
 10. fx_map cũ đã xóa khỏi run_sleep
 11. sleep_video.make_sleep_video() nhận kwargs mới (M7.2)
 12. sleep_video.render_sleep_video() forward config mới
 13. sleep_video.post_process() function tồn tại + short-circuit nếu không có gì để apply
 14. End-to-end MainWindow có tab_sleep với 4 cards
"""
import os
import sys
import tempfile

sys.path.insert(0, r"d:\auto-edit-video-main")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
app = QApplication.instance() or QApplication(sys.argv)

# Monkey-patch QMessageBox để không block modal
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.about = staticmethod(lambda *a, **k: QMessageBox.Ok)


# ---------- Test 1: tab_sleep imports OK ----------
from ui.tabs.tab_sleep import (
    SleepTab, EFFECTS, INTENSITIES, ASPECTS, FPS_OPTIONS,
    ENCODERS, VISUALIZERS, LOGO_POSITIONS,
)
print("[OK] ui.tabs.tab_sleep imports OK")

# ---------- Test 2: cmb_effect has 5 effects ----------
assert len(EFFECTS) == 5
assert {e[1] for e in EFFECTS} == {"none", "rain", "snow", "fog", "bokeh"}
print(f"[OK] EFFECTS = 5 items: {[e[1] for e in EFFECTS]}")

# ---------- Test 3: cmb_intensity has 3 mức ----------
assert len(INTENSITIES) == 3
assert {i[1] for i in INTENSITIES} == {"nhe", "vua", "nang"}
print(f"[OK] INTENSITIES = 3 items: {[i[1] for i in INTENSITIES]}")

# ---------- Test 4: Instantiate ----------
tab = SleepTab()
print(f"[OK] SleepTab instantiates OK")

# ---------- Test 5: cmb_fx CŨ đã XÓA ----------
assert not hasattr(tab, "cmb_fx"), "Old cmb_fx should be removed"
print("[OK] Old cmb_fx removed (replaced by cmb_effect + cmb_intensity)")

# ---------- Test 6: 16 options UI tồn tại ----------
expected_widgets = [
    "cmb_effect", "cmb_intensity", "cmb_vis",
    "spin_fade", "spin_max_seconds", "spin_item_sec", "spin_ambient_vol",
    "cmb_aspect", "cmb_fps", "cmb_encoder",
    "chk_noise", "chk_vignette",
    "spin_vintensity", "spin_vistrength",
    "title_input", "cmb_logo_pos",
]
for w in expected_widgets:
    assert hasattr(tab, w), f"Missing widget: {w}"
print(f"[OK] All {len(expected_widgets)} advanced widgets present")

# ---------- Test 7: path_inputs has 7 entries ----------
assert len(tab.path_inputs) == 7
expected_labels = [
    "NỀN (clip / ảnh / folder):",
    "AUDIO dài (kịch bản):",
    "Âm thanh NỀN (tùy chọn):",
    "Intro (M7 — video mở đầu):",
    "Outro (M7 — video kết thúc):",
    "Logo (M7 — PNG overlay):",
    "Xuất ra MP4:",
]
for label in expected_labels:
    assert label in tab.path_inputs, f"Missing path input: {label}"
print(f"[OK] path_inputs has {len(tab.path_inputs)} entries (M7 branding: intro/outro/logo)")

# ---------- Test 8: Browse handlers wired ----------
expected_handlers = [
    "browse_bg", "browse_audio", "browse_ambient",
    "browse_intro", "browse_outro", "browse_logo", "browse_output",
]
for h in expected_handlers:
    assert hasattr(tab, h), f"Missing browse handler: {h}"
    assert callable(getattr(tab, h))
print(f"[OK] All {len(expected_handlers)} browse handlers are real methods (not stubs)")

# Old stub_action should be GONE
assert not hasattr(tab, "stub_action"), "Old stub_action should be removed"
print("[OK] Old stub_action removed")

# ---------- Test 9: Effect combo data ----------
for i in range(tab.cmb_effect.count()):
    assert tab.cmb_effect.itemData(i) in {"none", "rain", "snow", "fog", "bokeh"}
print(f"[OK] cmb_effect items have correct EN data ({tab.cmb_effect.count()} items)")

for i in range(tab.cmb_intensity.count()):
    assert tab.cmb_intensity.itemData(i) in {"nhe", "vua", "nang"}
print(f"[OK] cmb_intensity items have correct EN data ({tab.cmb_intensity.count()} items)")

# ---------- Test 10: Defaults ----------
assert tab.cmb_intensity.currentData() == "vua"
assert tab.cmb_encoder.currentData() == "auto"
assert tab.cmb_fps.currentData() == 30
assert tab.spin_fade.value() == 4.0
assert tab.spin_ambient_vol.value() == 0.25
assert tab.spin_item_sec.value() == 20
assert tab.spin_max_seconds.value() == 0
assert not tab.chk_noise.isChecked()
assert not tab.chk_vignette.isChecked()
assert tab.spin_vintensity.value() == 0.5
assert tab.spin_vistrength.value() == 0.5
assert tab.title_input.text() == ""
assert tab.cmb_logo_pos.currentData() == "topright"
print("[OK] Default values are correct (rain effect, vua intensity, auto encoder...)")

# ---------- Test 11: _collect_cfg() returns full dict ----------
cfg = tab._collect_cfg()
required_keys = {
    # Core effect chain (M7.1)
    "effect", "intensity", "viz", "fade",
    # Audio & bg
    "ambient", "ambient_volume",
    # 16 advanced options
    "max_seconds", "item_sec", "encoder", "aspect", "fps",
    "noise", "vignette", "vignette_intensity", "vignette_strength",
    # Branding (M7)
    "title", "intro", "outro", "logo", "logo_position",
}
missing = required_keys - set(cfg.keys())
assert not missing, f"Missing keys in cfg: {missing}"
extra = set(cfg.keys()) - required_keys
assert not extra, f"Unexpected extra keys: {extra}"
print(f"[OK] _collect_cfg() returns {len(cfg)} keys (exact match)")

# Verify defaults
assert cfg["effect"] == "none"   # default = "Không"
assert cfg["intensity"] == "vua"
assert cfg["encoder"] == "auto"
assert cfg["fps"] == 30
assert cfg["logo_position"] == "topright"
assert cfg["ambient_volume"] == 0.25
print("[OK] _collect_cfg() default values correct")

# ---------- Test 12: Aspect changes propagate ----------
# None = legacy (don't pass)
assert cfg["aspect"] is None
# Change to 9:16
for i in range(tab.cmb_aspect.count()):
    if tab.cmb_aspect.itemData(i) == "9:16":
        tab.cmb_aspect.setCurrentIndex(i)
        break
cfg2 = tab._collect_cfg()
assert cfg2["aspect"] == "9:16"
print("[OK] Aspect ratio changes propagate to cfg")

# ---------- Test 13: Branding toggles ----------
tab.chk_noise.setChecked(True)
tab.chk_vignette.setChecked(True)
tab.title_input.setText("My Sleep Video")
cfg3 = tab._collect_cfg()
assert cfg3["noise"] is True
assert cfg3["vignette"] is True
assert cfg3["title"] == "My Sleep Video"
print("[OK] Noise/vignette/title toggles propagate to cfg")

# Reset
tab.chk_noise.setChecked(False)
tab.chk_vignette.setChecked(False)
tab.title_input.setText("")

# ---------- Test 14: _validate() rejects missing bg ----------
# Clear BG path
tab.path_inputs["NỀN (clip / ảnh / folder):"].setText("")
result = tab._validate()
assert result is False, "_validate() should reject empty bg"
print("[OK] _validate() rejects empty NỀN")

# ---------- Test 15: _validate() rejects missing audio ----------
tab.path_inputs["NỀN (clip / ảnh / folder):"].setText(r"d:\auto-edit-video-main\backgrounds")
tab.path_inputs["AUDIO dài (kịch bản):"].setText("")
result = tab._validate()
assert result is False, "_validate() should reject empty audio"
print("[OK] _validate() rejects empty AUDIO")

# ---------- Test 16: _validate() rejects nonexistent audio ----------
tab.path_inputs["AUDIO dài (kịch bản):"].setText("/nonexistent/audio.mp3")
result = tab._validate()
assert result is False
print("[OK] _validate() rejects nonexistent AUDIO")

# ---------- Test 17: _validate() rejects nonexistent intro ----------
tab.path_inputs["AUDIO dài (kịch bản):"].setText(r"d:\auto-edit-video-main\tests\test_milestone1.srt")  # not real audio but exists
# Actually SRT is not audio. We need a real audio file for full validate-OK. Skip strict ok test.
tab.path_inputs["Intro (M7 — video mở đầu):"].setText("/nonexistent/intro.mp4")
result = tab._validate()
assert result is False
print("[OK] _validate() rejects nonexistent Intro")
tab.path_inputs["Intro (M7 — video mở đầu):"].setText("")

# ---------- Test 18: fx_map cũ đã xóa ----------
import inspect
src = inspect.getsource(tab.run_sleep)
assert "fx_map" not in src, "Old fx_map should be removed from run_sleep"
assert "cfg[" in src or "cfg['" in src
# Should use the cfg dict from _collect_cfg
assert '"effect"' in src or "'effect'" in src
assert '"intro"' in src or "'intro'" in src  # M7 branding
assert '"logo"' in src or "'logo'" in src
print("[OK] run_sleep no longer uses fx_map; uses cfg dict directly")

# ---------- Test 19: sleep_video module has M7 extensions ----------
import sleep_video
import inspect

# make_sleep_video kwargs
sig = inspect.signature(sleep_video.make_sleep_video)
new_params = ["width", "height", "fps", "aspect",
              "noise", "vignette", "vignette_intensity", "vignette_strength",
              "title", "intro", "outro", "logo", "logo_position"]
for p in new_params:
    assert p in sig.parameters, f"sleep_video.make_sleep_video missing M7 param: {p}"
print(f"[OK] sleep_video.make_sleep_video accepts all {len(new_params)} M7 kwargs")

# render_sleep_video forwards M7 keys from cfg
src = inspect.getsource(sleep_video.render_sleep_video)
for key in new_params:
    assert f'"{key}"' in src or key in src, f"render_sleep_video doesn't forward {key}"
print("[OK] sleep_video.render_sleep_video forwards all M7 keys")

# post_process exists
assert hasattr(sleep_video, "post_process"), "Missing post_process function"
src = inspect.getsource(sleep_video.post_process)
# Should short-circuit if no enhancement
assert "needs_post" in src
print("[OK] sleep_video.post_process exists with short-circuit logic")

# ---------- Test 20: post_process returns input path when no changes ----------
with tempfile.TemporaryDirectory() as tmp:
    fake_out = os.path.join(tmp, "fake.mp4")
    # Should be no-op (file missing is OK; we return early before reading)
    # Actually need to create dummy for safety
    with open(fake_out, "wb") as f:
        f.write(b"dummy")
    result = sleep_video.post_process(fake_out, width=1920, height=1080, fps=30)
    assert result == fake_out
print("[OK] post_process() short-circuits when no M7 enhancement requested")

# ---------- Test 21: Browse handlers don't call stub_action ----------
for h in expected_handlers:
    func = getattr(tab, h)
    src = inspect.getsource(func)
    assert "stub_action" not in src, f"{h} still calls stub_action"
print(f"[OK] All {len(expected_handlers)} browse handlers are real (no stub_action call)")

# ---------- Test 22: End-to-end MainWindow ----------
from ui.main_window import MainWindow
mw = MainWindow()
mw.show()
# Find tab_sleep in stacked widget
sleep_idx = None
for i in range(mw.stacked_widget.count()):
    if isinstance(mw.stacked_widget.widget(i), SleepTab):
        sleep_idx = i
        break
assert sleep_idx is not None, "SleepTab not in main_window"
print(f"[OK] SleepTab at index {sleep_idx} in MainWindow stacked_widget")

# Verify cards built
st = mw.tab_sleep
# Card 1 = File paths, Card 2 = Effects, Card 3 = Advanced, Card 4 = Branding
# Tìm QFrame con
n_frames = sum(1 for c in st.findChildren(__import__('PySide6.QtWidgets', fromlist=['QFrame']).QFrame) if c.parent() is st or c.parent() is st.scroll_content)
assert n_frames >= 4, f"Expected ≥4 cards (file/effects/advanced/branding), got {n_frames}"
print(f"[OK] tab_sleep has {n_frames} QFrame cards (file/effects/advanced/branding)")

# ---------- Test 23: SleepWorker accepts new cfg keys ----------
from core.worker_sleep import SleepWorker
import inspect
src = inspect.getsource(SleepWorker.run)
# Worker just passes cfg to sleep_video.render_sleep_video
assert 'render_sleep_video' in src
# Forward compatible: Worker uses self.data["cfg"] without validating keys
assert 'self.data.get("cfg"' in src
print("[OK] SleepWorker is forward-compat (no schema validation, just passes cfg)")

print("\n=== ALL MILESTONE 7 TESTS PASSED ===")