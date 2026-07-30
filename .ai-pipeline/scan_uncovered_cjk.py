"""Scan and collect the unique CJK phrases in user-facing files. Then
identify which ones are NOT covered by the current i18n dictionary."""
import re
import json
from pathlib import Path

ROOT = Path("D:/AIWriteX")
EXCLUDE_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__",
    ".git", "dist", "build", ".next", "out",
    "static/lib", ".ai-pipeline", "knowledge",
    "translations_complete.json", "translations_map.json",
    "zh_strings_full.json", "zh_audit.json",
    "scripts/build_complete_translations.py",
    "scripts/build_translations.py",
}
CJK = re.compile(r'[一-鿿]')
SCAN_EXT = {".html", ".js", ".css"}

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    name = path.name.lower()
    if any(x in name for x in ("loader.js", "tsworker.js", "marked.min.js")):
        return True
    # Skip our own i18n infrastructure (it must keep CJK strings)
    if path.name in ("i18n_middleware.py",):
        return True
    return False

# Read existing dictionary
DICT_PATH = Path("D:/AIWriteX/src/ai_write_x/web/i18n_middleware.py")
import ast
dict_text = DICT_PATH.read_text(encoding="utf-8")
m = re.search(r"^CJK_VI_DICTIONARY:\s*List\[Tuple\[str,\s*str\]\]\s*=\s*\[(.+?)\]", dict_text, re.DOTALL | re.MULTILINE)
list_text = "[" + m.group(1) + "]"
dict_data = ast.literal_eval(list_text)
existing = {src for src, _ in dict_data}

# Scan all files for CJK-only phrases (1-6 chars long)
unique_cjk: dict[str, int] = {}
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    if should_skip(p):
        continue
    if p.suffix.lower() not in SCAN_EXT:
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        continue
    # Find contiguous CJK runs
    for m in CJK.finditer(text):
        start = m.start()
        # Find end of run
        end = start
        while end < len(text) and CJK.match(text[end]):
            end += 1
        phrase = text[start:end]
        # Skip very long phrases (likely code block comments)
        if len(phrase) > 8:
            continue
        unique_cjk[phrase] = unique_cjk.get(phrase, 0) + 1

# Print all unique phrases, mark which are in dictionary
print(f"Total unique CJK phrases: {len(unique_cjk)}")
print()
in_dict = []
not_in_dict = []
for phrase, count in sorted(unique_cjk.items(), key=lambda kv: -kv[1]):
    if phrase in existing:
        in_dict.append((phrase, count))
    else:
        not_in_dict.append((phrase, count))

print(f"In dictionary: {len(in_dict)}")
print(f"NOT in dictionary: {len(not_in_dict)}")
print()
print("--- NOT in dictionary (top by frequency) ---")
for p, c in not_in_dict[:50]:
    print(f"  {c:4}x  {repr(p)}")