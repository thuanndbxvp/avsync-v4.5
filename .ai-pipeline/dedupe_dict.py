"""Dedupe the i18n dictionary (first-occurrence wins)."""
import re

with open("src/ai_write_x/web/i18n_middleware.py", encoding="utf-8") as f:
    src = f.read()

m = re.search(
    r"CJK_VI_DICTIONARY: List\[Tuple\[str, str\]\] = \[(.*?)\]\n",
    src,
    re.DOTALL,
)
if not m:
    raise SystemExit("dict block not found")

block = m.group(1)
entries = re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', block)
print(f"parsed {len(entries)} entries")

seen = {}
deduped = []
for s, v in entries:
    if s in seen:
        continue
    seen[s] = v
    deduped.append((s, v))
print(f"deduped to {len(deduped)}")

# Sanity: verify translation consistency for duplicates
mismatches = 0
for s, v in entries:
    if seen.get(s) and seen[s] != v:
        mismatches += 1
print(f"translations inconsistent across duplicates: {mismatches}")

new_block = "\n".join(f'    ("{s}", "{v}"),' for s, v in deduped)
new_src = src[:m.start(1)] + new_block + src[m.end(1):]

with open("src/ai_write_x/web/i18n_middleware.py", "w", encoding="utf-8") as f:
    f.write(new_src)
print("rewritten")