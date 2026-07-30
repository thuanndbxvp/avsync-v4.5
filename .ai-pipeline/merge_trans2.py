#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Merge new translations into i18n_middleware.py CJK_VI_DICTIONARY."""
import sys, re, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

MIDDLEWARE = Path('D:/AIWriteX/src/ai_write_x/web/i18n_middleware.py')
NEW_TRANS = Path('D:/AIWriteX/new_trans.json')

new = json.loads(NEW_TRANS.read_text('utf-8'))
print(f'New translations to add: {len(new)}')

src = MIDDLEWARE.read_text('utf-8')

# Find the dictionary block
m = re.search(r'(CJK_VI_DICTIONARY:\s*List\[Tuple\[str,\s*str\]\]\s*=\s*\[)(.+?)(\n\])', src, re.DOTALL)
if not m:
    print('Could not find dictionary block!')
    sys.exit(1)

prefix = m.group(1)  # CJK_VI_DICTIONARY...
dict_body = m.group(2)   # all the tuples
suffix = m.group(3)   # \n]

# Parse existing entries
existing = set()
for pm in re.finditer(r'\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)', dict_body):
    existing.add(pm.group(1))

to_add = [(cn, vi) for cn, vi in new.items() if cn not in existing]
print(f'Already in dict: {len(new) - len(to_add)}, To add: {len(to_add)}')

if not to_add:
    print('All already translated!')
    sys.exit(0)

# Build new entries
new_entries = []
for cn, vi in to_add:
    # Escape any " in the source string
    new_entries.append(f'    ("{cn}", "{vi}")')

# Find last tuple in dict_body to add comma after
if not dict_body.strip().endswith(','):
    # Add comma to last existing entry
    dict_body = dict_body.rstrip() + ',\n'

new_block = '\n'.join(new_entries)
new_dict = prefix + dict_body + new_block + suffix

# Replace in source
new_src = src[:m.start()] + new_dict + src[m.end():]

MIDDLEWARE.write_text(new_src, 'utf-8')
print(f'Updated {MIDDLEWARE} with {len(to_add)} new translations')
