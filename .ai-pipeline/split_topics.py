"""Split each topic's outline into a short description + remaining outline.

Strategy: take the first 1-2 sentences as 'description', keep the rest as
'outline'. Falls back gracefully if the source text has only one sentence.
"""
import json
import re
from pathlib import Path

SRC = Path("src/ai_write_x/niches/data/finance_ideas_raw.json")
DST = Path("src/ai_write_x/niches/data/finance_ideas_raw.json")

# Also keep the seeds file in sync.
SEEDS_SRC = Path("src/content/seeds/finance_ideas.json")

SPLIT_CHARS = re.compile(r"(?<=[.!?。!?])\s+")

def split_text(text: str) -> tuple[str, str]:
    """Return (description, outline).

    Heuristic: first sentence -> description, rest -> outline.
    If outline is empty, the description becomes the full text.
    """
    text = text.strip()
    if not text:
        return "", ""
    # Split on common sentence boundaries (period, exclamation, question mark,
    # Vietnamese full stops). Try to keep quoted phrases intact.
    parts = SPLIT_CHARS.split(text, maxsplit=1)
    if len(parts) == 2:
        desc = parts[0].strip()
        rest = parts[1].strip()
        if len(desc) < 30 or len(desc) > len(text) * 0.7:
            # Description too short or too long, keep whole text in outline
            return "", text
        return desc, rest
    return "", text

def is_already_split(item: dict) -> bool:
    """Detect if item was already split (has separate description+outline)."""
    return "description" in item and "outline" in item

def transform(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        # If already split (idempotent run), keep as-is
        if is_already_split(it):
            new = dict(it)
        else:
            outline = it.get("outline", "").strip()
            desc, outline = split_text(outline)
            # Re-arrange so the JSON order is consistent
            new = {
                "category": it.get("category"),
                "title": it.get("title"),
                "branch": it.get("branch"),
                "description": desc,
                "outline": outline,
            }
            # Preserve id if present
            if "id" in it and it["id"] is not None:
                new["id"] = it["id"]
            # Preserve tags if present
            if "tags" in it:
                new["tags"] = it["tags"]
        out.append(new)
    return out

def main():
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    new_raw = transform(raw)
    DST.write_text(
        json.dumps(new_raw, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(new_raw)} items to {DST}")

    # Also sync seeds file
    if SEEDS_SRC.exists():
        seeds = json.loads(SEEDS_SRC.read_text(encoding="utf-8"))
        new_seeds = transform(seeds)
        SEEDS_SRC.write_text(
            json.dumps(new_seeds, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {len(new_seeds)} items to {SEEDS_SRC}")

    # Show samples
    print("\n--- samples (first 5) ---")
    for it in new_raw[:5]:
        print(f"  [{it.get('id', '?')}] {it['title'][:60]}")
        print(f"    DESC: {it['description']}")
        print(f"    OUTL: {it['outline'][:100]}...")

    # Stats
    desc_count = sum(1 for it in new_raw if it["description"])
    print(f"\nTopics with description: {desc_count}/{len(new_raw)}")

if __name__ == "__main__":
    main()