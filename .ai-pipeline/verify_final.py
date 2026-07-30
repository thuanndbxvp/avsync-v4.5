import json
for p in ['src/content/seeds/finance_ideas.json', 'src/ai_write_x/niches/data/finance_ideas_raw.json']:
    data = json.loads(open(p, encoding='utf-8').read())
    desc_count = sum(1 for it in data if it.get('description'))
    print(f'{p}:')
    print(f'  items: {len(data)}')
    print(f'  with description: {desc_count}')
    print(f'  sample id 1 desc: {data[0].get("description", "")[:80]}')
    print(f'  sample id 1 outl: {data[0].get("outline", "")[:80]}')
    print()