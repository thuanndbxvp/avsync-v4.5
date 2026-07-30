"""Smoke-test i18n module."""
import sys
sys.path.insert(0, ".")
from src.ai_write_x.web.i18n import t, available_locales, resolve_locale

print("available_locales:", available_locales())
print()

cases = [
    ("m_056c9b52", "vi", "Vui lòng chọn một danh mục trước"),
    ("m_056c9b52", "en", "Please select a category first"),
    ("m_056c9b52", "zh", "请先选择一个分类"),
    ("m_07c2859e", "vi", "Thoát chế độ hàng loạt"),
    ("m_07c2859e", "en", "Exit batch mode"),
    ("DOES_NOT_EXIST", "vi", "FALLBACK OK"),
]
for key, lang, expected in cases:
    actual = t(key, lang=lang)
    ok = "OK" if expected in actual else "FAIL"
    print(f"  [{ok}] {key} @ {lang} -> {actual!r}")

print()
print("resolve_locale tests:")
for lang, accept in [
    (None, "vi-VN,vi;q=0.9,en;q=0.8"),
    ("en", "zh-CN,zh;q=0.9"),
    (None, "fr-FR,fr;q=0.9"),
    (None, None),
]:
    print(f"  lang={lang!r} accept={accept!r} -> {resolve_locale(lang, accept)!r}")