#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate missing translations using word-level substitution."""
import sys, re, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

WORD = json.loads(Path(__file__).parent.joinpath('word_map.json').read_text('utf-8'))

def trans(phrase):
    """Translate a Chinese phrase to Vietnamese using word substitution."""
    result = phrase
    for cn, vi in sorted(WORD.items(), key=lambda x: -len(x[0])):
        result = result.replace(cn, vi)
    return result.strip().rstrip(',').rstrip(';')

MISSING = Path('D:/AIWriteX/missing_cjk.json')
missing = json.loads(MISSING.read_text('utf-8'))

output = {}
for p in missing:
    t = trans(p)
    if t and t != p:
        output[p] = t

OUT = Path('D:/AIWriteX/new_trans.json')
OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), 'utf-8')
print(f'Translated {len(output)}/{len(missing)} phrases -> {OUT}')
