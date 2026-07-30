"""Scan all user-facing files for CJK characters (Chinese).
Excludes vendor libraries (Monaco, Marked, jQuery, Bootstrap).
"""
import re
from pathlib import Path

ROOT = Path("D:/AIWriteX")
EXCLUDE_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__",
    ".git", "dist", "build", ".next", "out",
    "static/lib", "static/lib/monaco", "static/lib/marked",
}
CJK = re.compile(r'[一-鿿]')

# These file extensions we DO scan
SCAN_EXT = {".html", ".js", ".css", ".py", ".json", ".md"}

# JS files to EXCLUDE (vendor libs)
JS_EXCLUDE = {
    "loader.js", "tsWorker.js", "marked.min.js", "jquery", "bootstrap",
}

# Files inside static/lib are excluded
def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    # Also skip monaco/marked even if not under static/lib for safety
    name = path.name.lower()
    if any(x in name for x in JS_EXCLUDE):
        return True
    return False

results: dict[Path, list[tuple[int, str]]] = {}
total_lines = 0
total_files = 0
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
    file_hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if CJK.search(line):
            file_hits.append((i, line.strip()))
    if file_hits:
        results[p] = file_hits
        total_files += 1
        total_lines += len(file_hits)

# Print summary
print(f"FILES WITH CJK: {total_files}")
print(f"TOTAL CJK LINES: {total_lines}")
print()
for p, hits in sorted(results.items(), key=lambda kv: -len(kv[1]))[:50]:
    print(f"--- {p.relative_to(ROOT)} ({len(hits)} lines) ---")
    for ln, content in hits[:5]:
        print(f"  L{ln}: {content[:120]}")
    if len(hits) > 5:
        print(f"  ... and {len(hits)-5} more lines")
    print()