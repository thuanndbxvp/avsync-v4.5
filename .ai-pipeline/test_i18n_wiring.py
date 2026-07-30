"""Verify i18n endpoints registered in the FastAPI app."""
import sys
sys.path.insert(0, ".")

from src.ai_write_x.web.app import app

i18n_paths = []
for r in app.routes:
    path = getattr(r, "path", None)
    if path and "/i18n" in path:
        methods = getattr(r, "methods", None)
        i18n_paths.append((path, methods))

print(f"i18n endpoints: {i18n_paths}")
print()

# Test the actual translate logic via the live i18n module
from src.ai_write_x.web.i18n import t
samples = [
    ("m_056c9b52", "vi"),
    ("m_07c2859e", "en"),
    ("m_056c9b52", "zh"),
]
for key, lang in samples:
    print(f"  t({key!r}, lang={lang!r}) -> {t(key, lang=lang)!r}")