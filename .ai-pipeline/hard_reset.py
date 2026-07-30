"""Hard-reset both finance_ideas files using ORIGINAL_OUTLINES."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from restore_outlines import ORIGINAL_OUTLINES

# Also need category, branch, title. Use seeds (which still has them).
SEEDS = Path("src/content/seeds/finance_ideas.json")
RAW = Path("src/ai_write_x/niches/data/finance_ideas_raw.json")

seeds = json.loads(SEEDS.read_text(encoding="utf-8"))

new_items = []
for it in seeds:
    item_id = it.get("id")
    if item_id and item_id in ORIGINAL_OUTLINES:
        # Use the original outline from the captured data
        new_items.append({
            "id": item_id,
            "category": it.get("category"),
            "title": it.get("title"),
            "branch": it.get("branch"),
            "outline": ORIGINAL_OUTLINES[item_id],
        })
    else:
        # Fallback: use whatever is in seeds (shouldn't happen)
        new_items.append(it)

# Sync both files
SEEDS.write_text(json.dumps(new_items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Restored {SEEDS}: {len(new_items)} items")

# Raw file uses no id, no tags
raw_items = [
    {
        "category": it["category"],
        "title": it["title"],
        "branch": it["branch"],
        "outline": it["outline"],
    }
    for it in new_items
]
RAW.write_text(json.dumps(raw_items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Restored {RAW}: {len(raw_items)} items")

# Verify
print()
print("Sample id 1:")
print(f"  outline: {new_items[0]['outline']}")