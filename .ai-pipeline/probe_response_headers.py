import urllib.request
req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Language': 'vi-VN,vi;q=0.9'})
r = urllib.request.urlopen(req)
print('Response headers:')
for k, v in r.headers.items():
    print(f'  {k}: {v}')
print()
print('First 200 chars of HTML:')
print(r.read().decode('utf-8')[:200])