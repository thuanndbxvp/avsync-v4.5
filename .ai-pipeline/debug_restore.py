import json
from pathlib import Path

# Check what restore did
p = Path('src/ai_write_x/niches/data/finance_ideas_raw.json')
data = json.loads(p.read_text(encoding='utf-8'))
print('Before restore, id 1 outline:', repr(data[0].get('outline', '<no outline>')[:60]))
print('id field:', data[0].get('id'))
print()

# Check if id field is missing (which would cause restore to do nothing)
print('Has id key?', 'id' in data[0])
print('All keys:', list(data[0].keys()))