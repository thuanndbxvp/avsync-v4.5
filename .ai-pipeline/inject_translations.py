"""Inject the new translations into the i18n_middleware.py dictionary."""
import json
from pathlib import Path

NEW = json.loads(Path(".ai-pipeline/new_translations.json").read_text(encoding="utf-8"))
DICT_PATH = Path("src/ai_write_x/web/i18n_middleware.py")

text = DICT_PATH.read_text(encoding="utf-8")

# Find the closing ] of CJK_VI_DICTIONARY
# It ends with: ("搜 索", "Tìm"),]
# We inject before the final ]
lines_to_add = []
for entry in NEW:
    cjk = entry["cjk"]
    vi = entry["vi"]
    # Escape quotes
    vi_escaped = vi.replace("\\", "\\\\").replace('"', '\\"')
    lines_to_add.append(f'    ("{cjk}", "{vi_escaped}"),')

# Insert before the final line ending with "Tìm"),]
marker = '    ("搜 索", "Tìm"),]'
if marker not in text:
    raise RuntimeError("Could not find dictionary end marker")

new_block = "\n".join(lines_to_add) + "\n"
replacement = new_block + marker
new_text = text.replace(marker, replacement, 1)

DICT_PATH.write_text(new_text, encoding="utf-8")
print(f"Injected {len(NEW)} new translations")