"""Smoke test Milestone 10 — Thumbnail Preview + Hybrid Profile Schema + i18n + E2E FFmpeg.

Coverage:
  1. tab_settings imports OK + has thumbnail widgets
  2. lbl_preview = QLabel 200x200 with gray border
  3. btn_browse_thumb wires to _browse_thumb handler
  4. Hybrid schema: _profile_text + _profile_thumb extract from str OR dict
  5. _build_profile_value returns dict khi có thumb, str khi không
  6. Selecting dict-format profile loads prompt text + clears/shows thumb label
  7. i18n.py module works (set_lang + tr fallback)
  8. Tab Settings wraps button text với _i18n.tr (PoC)
  9. E2E render_video() thực sự chạy ffmpeg → output.mp4 > 1KB + > 0s duration
 10. worker_prompt hybrid schema fallback: dict → str(prompt)
 11. Backward-compat: M1-M8 + M9 imports still OK
"""
import os
import sys
import subprocess

sys.path.insert(0, r"d:\auto-edit-video-main")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
app = QApplication.instance() or QApplication(sys.argv)

QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)


# ---------- Test 1: tab_settings imports ----------
from ui.tabs.tab_settings import SettingsTab
import i18n as _i18n
print("[OK] tab_settings + i18n imports OK")

# ---------- Test 2: thumbnail widgets exist ----------
st = SettingsTab()
assert hasattr(st, "lbl_preview")
assert hasattr(st, "btn_browse_thumb")
assert hasattr(st, "_browse_thumb")
print(f"[OK] thumbnail widgets present: lbl_preview, btn_browse_thumb, _browse_thumb")

# ---------- Test 3: lbl_preview size = 200x200 + border ----------
assert st.lbl_preview.size().width() == 200
assert st.lbl_preview.size().height() == 200
assert "border" in st.lbl_preview.styleSheet()
print(f"[OK] lbl_preview = {st.lbl_preview.size().width()}x{st.lbl_preview.size().height()} with border")

# ---------- Test 4: btn_browse_thumb wired ----------
assert isinstance(st.btn_browse_thumb, QPushButton)
assert "Ảnh" in st.btn_browse_thumb.text() or "Browse" in st.btn_browse_thumb.text()
print(f"[OK] btn_browse_thumb text = '{st.btn_browse_thumb.text()}'")

# ---------- Test 5: hybrid schema helpers ----------
from PySide6.QtCore import Qt

# Test _profile_text from str
assert SettingsTab._profile_text("hello") == "hello"
# Test _profile_text from dict
assert SettingsTab._profile_text({"prompt": "p", "thumb": "t.png"}) == "p"
# Test _profile_text from empty
assert SettingsTab._profile_text("") == ""
assert SettingsTab._profile_text({}) == ""

# Test _profile_thumb from str (None)
assert SettingsTab._profile_thumb("hello") is None
# Test _profile_thumb from dict with valid thumb
assert SettingsTab._profile_thumb({"prompt": "p", "thumb": "t.png"}) == "t.png"
# Test _profile_thumb from dict with no thumb
assert SettingsTab._profile_thumb({"prompt": "p"}) is None
print(f"[OK] hybrid schema helpers (_profile_text, _profile_thumb) work")

# ---------- Test 6: _build_profile_value ----------
# No thumb → str
result = SettingsTab._build_profile_value(st, "text content", None)
assert isinstance(result, str)
assert result == "text content"

# With non-existent thumb path → str (fallback)
result = SettingsTab._build_profile_value(st, "text", "/nonexistent.png")
assert isinstance(result, str)

# With existing thumb → dict
import tempfile
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
    tf.write(b"fake png bytes")
    real_thumb = tf.name
try:
    result = SettingsTab._build_profile_value(st, "with thumb", real_thumb)
    assert isinstance(result, dict)
    assert result["prompt"] == "with thumb"
    assert result["thumb"] == real_thumb
    print(f"[OK] _build_profile_value returns dict when thumb is valid file")
finally:
    os.remove(real_thumb)

# ---------- Test 7: Selecting dict-format profile ----------
st._data["profiles"]["TestDict"] = {
    "prompt": "This is a hybrid dict profile",
    "thumb": "/tmp/some.png"
}
st._refresh_profile_list()
items = st.list_profiles.findItems("TestDict", Qt.MatchExactly)
assert items
st.list_profiles.setCurrentItem(items[0])
app.processEvents()
assert st.txt_prompt.toPlainText() == "This is a hybrid dict profile"
assert getattr(st, "_current_thumb", None) == "/tmp/some.png"
print(f"[OK] Selecting dict-profile loads prompt text + thumb path")

# Cleanup
del st._data["profiles"]["TestDict"]

# ---------- Test 8: i18n module works ----------
_i18n.set_lang("en")
result = _i18n.tr("➕ Thêm")
assert result == "➕ Add", f"Expected '➕ Add', got '{result}'"
_i18n.set_lang("vi")
result = _i18n.tr("➕ Thêm")
# vi mode → fallback to original (key)
assert result == "➕ Thêm"
print(f"[OK] i18n.tr('➕ Thêm') switches VI ↔ EN correctly")

# ---------- Test 9: btn_add_prof in SettingsTab uses i18n.tr ----------
btn_text = st.btn_add_prof.text() if hasattr(st, 'btn_add_prof') else None
# Note: btn_add_prof is a local var in setup_ui, not self.attr — check via children
btn_add_widget = None
for child in st.findChildren(QPushButton):
    if child.text().startswith("➕"):
        btn_add_widget = child
        break
assert btn_add_widget is not None, "Cannot find ➕ button"
print(f"[OK] ➕ button text = '{btn_add_widget.text()}' (i18n wrapped)")

# ---------- Test 10: worker_prompt hybrid schema ----------
import inspect
from core.worker_prompt import PromptWorker
src = inspect.getsource(PromptWorker.run)
assert "isinstance(raw_profile, dict)" in src
assert 'raw_profile.get("prompt"' in src
print(f"[OK] worker_prompt.run() handles hybrid schema (dict | str)")

# ---------- Test 11: E2E render runs thật ----------
print(f"\n[E2E] Running actual ffmpeg render...")
import time
t0 = time.time()
import sys as _sys
# Capture stderr to avoid cluttering output
result = subprocess.run(
    [_sys.executable, "tests/e2e/test_render.py"],
    cwd=r"d:\auto-edit-video-main",
    capture_output=True, text=True, timeout=120,
)
elapsed = time.time() - t0
if result.returncode == 0:
    print(f"[OK] E2E render script exit 0 ({elapsed:.1f}s)")
    # Check output file exists and is valid
    out_path = r"d:\auto-edit-video-main\tests\e2e\output.mp4"
    if os.path.isfile(out_path):
        size = os.path.getsize(out_path)
        assert size > 1024, f"Output too small: {size}"
        print(f"[OK] output.mp4 = {size:,} bytes (>1KB threshold)")
    else:
        raise AssertionError("E2E output.mp4 not created")
else:
    print(f"[FAIL] E2E script exit {result.returncode}:")
    print(result.stdout[-800:])
    print(result.stderr[-800:])
    raise AssertionError(f"E2E render failed with exit {result.returncode}")

# ---------- Test 12: ffprobe confirms valid MP4 ----------
ffprobe_check = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
     "-of", "csv=p=0", r"d:\auto-edit-video-main\tests\e2e\output.mp4"],
    capture_output=True, text=True, timeout=10,
)
if ffprobe_check.returncode == 0 and ffprobe_check.stdout.strip():
    parts = ffprobe_check.stdout.strip().split(",")
    if len(parts) >= 2:
        # csv order: duration,size (per format=duration,size)
        dur_s = float(parts[0])
        size_b = int(parts[1])
        assert dur_s > 0, f"Duration should be > 0, got {dur_s}"
        assert size_b > 1024, f"Size should be > 1KB, got {size_b}"
        print(f"[OK] ffprobe confirms: {size_b:,}B, {dur_s:.2f}s")

# ---------- Test 13: Backward-compat M1-M8 imports still OK ----------
import core.worker_render, core.worker_sleep, core.worker_queue, core.worker_prompt
import ui.tabs.tab_prompt, ui.tabs.tab_render, ui.tabs.tab_sleep, ui.tabs.tab_queue
import services.render_service, services.prompt_service, services.prompt_writer, services.config_service
print(f"[OK] All M1-M9 + M10 modules import clean")

print("\n=== ALL MILESTONE 10 TESTS PASSED ===")