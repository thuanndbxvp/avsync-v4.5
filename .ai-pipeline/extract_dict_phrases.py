"""Properly extract CJK phrases from the dictionary file using AST."""
import ast
import re
from pathlib import Path

DICT_PATH = Path("src/ai_write_x/web/i18n_middleware.py")
text = DICT_PATH.read_text(encoding="utf-8")

# Find the CJK_VI_DICTIONARY assignment
m = re.search(r"^CJK_VI_DICTIONARY:\s*List\[Tuple\[str,\s*str\]\]\s*=\s*\[(.+?)\]", text, re.DOTALL | re.MULTILINE)
if not m:
    print("Could not find dictionary")
    raise SystemExit(1)
list_text = "[" + m.group(1) + "]"
data = ast.literal_eval(list_text)
existing = {src for src, _ in data}
print(f"Total entries in dict: {len(data)}")
print(f"Unique source phrases: {len(existing)}")

# Write to a file for next step
import pickle
pickle.dump(existing, open(".ai-pipeline/dict_phrases.pkl", "wb"))
print("Wrote .ai-pipeline/dict_phrases.pkl")