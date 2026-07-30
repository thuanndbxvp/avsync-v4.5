"""Recover the original outline by concatenating description + outline.

When the split script ran the first time, it correctly split into
description + outline. When it ran a second time, it lost description
because the script read the already-split file. This script reconstructs
the original by joining them back.
"""
import json
from pathlib import Path

PATHS = [
    Path("src/ai_write_x/niches/data/finance_ideas_raw.json"),
    Path("src/content/seeds/finance_ideas.json"),
]

for p in PATHS:
    data = json.loads(p.read_text(encoding="utf-8"))
    fixed = []
    for it in data:
        desc = it.get("description", "").strip()
        outl = it.get("outline", "").strip()
        if desc:
            # Reconstruct the original outline: description + ". " + outline
            original_outline = desc + ". " + outl if outl else desc
        else:
            original_outline = outl
        new = dict(it)
        new["outline"] = original_outline
        # Drop description for now; we'll re-split properly
        new.pop("description", None)
        fixed.append(new)
    p.write_text(json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recovered {p}: {len(fixed)} items")

# Verify by checking first item
print("\nSample first item outline:")
data = json.loads(PATHS[0].read_text(encoding="utf-8"))
print(data[0]["outline"])