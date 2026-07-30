"""Debug parser."""
from pathlib import Path
import sys

SRC = Path(r"D:\Dark-Frontiers\constants.ts")
text = SRC.read_text(encoding="utf-8")

start = text.find("FINANCE_IDEAS")
bracket_start = -1
search_from = start
while True:
    idx = text.find("[", search_from)
    if idx == -1:
        break
    if text[idx + 1] == "]":
        search_from = idx + 2
        continue
    bracket_start = idx
    break

depth = 0
i = bracket_start
in_str = False
str_ch = None
while i < len(text):
    ch = text[i]
    if in_str:
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == str_ch:
            in_str = False
        i += 1
        continue
    if ch in ('"', "'"):
        in_str = True
        str_ch = ch
        i += 1
        continue
    if ch == "[":
        depth += 1
    elif ch == "]":
        depth -= 1
        if depth == 0:
            break
    i += 1
array_text = text[bracket_start : i + 1]

sys.path.insert(0, r"D:\AIWriteX\.ai-pipeline")
from extract_finance_ideas import parse_ts_object, split_top_level_objects

objs = split_top_level_objects(array_text)
print(f"Found {len(objs)} objects")
print()
print("First object:")
print(repr(objs[0][:500]))
print()
parsed = parse_ts_object(objs[0])
print("Parsed:")
for k, v in parsed.items():
    print(f"  {k!r}: {v[:80] if isinstance(v, str) else v!r}")