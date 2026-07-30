"""Extract FINANCE_IDEAS từ D:\\Dark-Frontiers\\constants.ts sang JSON.

Approach: regex-extract each top-level object's text, then regex-extract
key/value pairs from each object's text.  Output is a list of 152 dicts.
"""
import re
import json
from pathlib import Path

SRC = Path(r"D:\Dark-Frontiers\constants.ts")
DST = Path(r"D:\AIWriteX\src\content\seeds\finance_ideas.json")
text = SRC.read_text(encoding="utf-8")

# Locate the array opening bracket — skip TypeScript type annotation `[]`.
start = text.find("FINANCE_IDEAS")
bracket_start = -1
search_from = start
while True:
    idx = text.find("[", search_from)
    if idx == -1:
        break
    if idx + 1 < len(text) and text[idx + 1] == "]":
        search_from = idx + 2
        continue
    bracket_start = idx
    break

assert bracket_start != -1

# Walk forward to matching close bracket.
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


def split_top_level_objects(s):
    """Split an array of objects at top-level commas (depth-0 commas)."""
    objs = []
    depth = 0
    start = None
    in_str = False
    str_ch = None
    for i, ch in enumerate(s):
        if in_str:
            if ch == "\\" and i + 1 < len(s):
                continue  # skip escaped char
            if ch == str_ch:
                in_str = False
            continue
        if ch in ('"', "'"):
            in_str = True
            str_ch = ch
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                objs.append(s[start : i + 1])
                start = None
    return objs


def parse_object(s):
    """Extract `key: "value"` and `key: bareword` pairs from a TS object literal."""
    out = {}
    # Match: key: "value"
    for m in re.finditer(r'(\w+)\s*:\s*"((?:\\.|[^"\\])*)"', s):
        out[m.group(1)] = m.group(2)
    # Match: key: bareword (number or enum)
    for m in re.finditer(r'(\w+)\s*:\s*([A-Za-z0-9_.\-]+)(?=\s*[,\n}])', s):
        if m.group(1) in out:
            continue
        out[m.group(1)] = m.group(2)
    return out


objs = split_top_level_objects(array_text)
print(f"Found {len(objs)} objects")

entries = []
for idx, obj_text in enumerate(objs, start=1):
    parsed = parse_object(obj_text)
    if not parsed.get("title"):
        continue
    entries.append({
        "id": idx,
        "category": parsed.get("category", ""),
        "title": parsed.get("title", ""),
        "branch": parsed.get("branch", "analytical"),
        "outline": parsed.get("outline", ""),
        "tags": ["finance", parsed.get("branch", "analytical")],
    })

print(f"Parsed {len(entries)} finance ideas")
DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {DST}")

# Sanity-check sample
print()
print("Sample entries:")
for e in entries[:3]:
    print(f"  #{e['id']:3d} [{e['branch']:12s}] {e['title'][:60]}")

from collections import Counter
print()
print("Branch distribution:")
for b, c in Counter(e["branch"] for e in entries).most_common():
    print(f"  {b:14s} {c:4d}")
print()
print("Category distribution:")
for cat, c in Counter(e["category"] for e in entries).most_common():
    print(f"  {cat:30s} {c:4d}")