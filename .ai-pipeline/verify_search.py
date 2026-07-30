import urllib.request, json
# Search for "Bitcoin" — should match title, outline, or description
with urllib.request.urlopen('http://localhost:8000/api/topics?q=Bitcoin&limit=5') as r:
    data = json.loads(r.read().decode('utf-8'))
print(f'Total matching "Bitcoin": {data["total"]}')
for item in data['items']:
    print(f'  [{item["id"]}] {item["title"][:60]}')

print()

# Search for "FOMO" (might be in description only)
with urllib.request.urlopen('http://localhost:8000/api/topics?q=FOMO&limit=5') as r:
    data = json.loads(r.read().decode('utf-8'))
print(f'Total matching "FOMO": {data["total"]}')
for item in data['items']:
    print(f'  [{item["id"]}] {item["title"][:60]}')
    if 'FOMO' in item.get('description', ''):
        print(f'      [match in description] {item["description"][:100]}')
    elif 'FOMO' in item.get('outline', ''):
        print(f'      [match in outline] {item["outline"][:100]}')