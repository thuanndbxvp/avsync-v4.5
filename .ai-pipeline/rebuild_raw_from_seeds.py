"""Rebuild finance_ideas_raw.json from seeds/finance_ideas.json, which still
has the original outlines plus IDs.
"""
import json
from pathlib import Path

SEEDS = Path("src/content/seeds/finance_ideas.json")
RAW = Path("src/ai_write_x/niches/data/finance_ideas_raw.json")

seeds = json.loads(SEEDS.read_text(encoding="utf-8"))
raw = []
for it in seeds:
    # Strip id and tags (runtime data only needs these 5 fields)
    raw.append({
        "category": it.get("category"),
        "title": it.get("title"),
        "branch": it.get("branch"),
        "description": it.get("description", ""),
        "outline": it.get("outline", ""),
    })

RAW.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Rebuilt {RAW} with {len(raw)} items from seeds")

# Verify
first = raw[0]
print(f"Sample: {first['title']}")
print(f"  desc: {first['description']}")
print(f"  outl: {first['outline'][:80]}...")