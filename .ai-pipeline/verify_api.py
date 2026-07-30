import urllib.request, json
with urllib.request.urlopen('http://localhost:8000/api/topics?limit=2') as r:
    data = json.loads(r.read().decode('utf-8'))
for item in data['items']:
    print(f'id={item["id"]} | title={item["title"]}')
    print(f'  branch: {item["branch"]}')
    print(f'  description: {item["description"]}')
    print(f'  outline: {item["outline"][:120]}')
    print()