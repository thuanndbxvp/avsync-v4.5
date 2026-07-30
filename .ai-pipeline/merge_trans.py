#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Merge new translations into i18n_middleware.py CJK_VI_DICTIONARY."""
import sys, re, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

MIDDLEWARE = Path('D:/AIWriteX/src/ai_write_x/web/i18n_middleware.py')
NEW_TRANS = Path('D:/AIWriteX/new_trans.json')

# Read new translations
new = json.loads(NEW_TRANS.read_text('utf-8'))
print(f'New translations to add: {len(new)}')

# Read existing middleware
src = MIDDLEWARE.read_text('utf-8')

# Check which phrases already exist
existing = set()
for m in re.finditer(r'\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)', src):
    existing.add(m.group(1))
    
to_add = [(cn, vi) for cn, vi in new.items() if cn not in existing]
print(f'Already in dict: {len(new) - len(to_add)}, To add: {len(to_add)}')

if not to_add:
    print('All already translated!')
    sys.exit(0)

# Build new entries
new_entries = []
for cn, vi in to_add:
    new_entries.append(f'    ("{cn}", "{vi}")')

# Find insertion point (before the closing bracket)
insert_at = src.rfind(']')
if insert_at == -1:
    print('Could not find closing bracket!')
    sys.exit(1)

# Insert new entries
indent = '\n'
new_block = '\n'.join(new_entries)
new_src = src[:insert_at] + ',\n' + new_block + '\n' + src[insert_at:]

# Write back
MIDDLEWARE.write_text(new_src, 'utf-8')
print(f'Updated {MIDDLEWARE} with {len(to_add)} new translations')
