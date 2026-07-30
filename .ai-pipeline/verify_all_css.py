import urllib.request, re

req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Language': 'vi-VN,vi;q=0.9'})
r = urllib.request.urlopen(req)
html = r.read().decode('utf-8')

# Extract all CSS link hrefs
hrefs = re.findall(r'<link rel="stylesheet" href="([^"]+)"', html)
print(f'CSS files referenced in HTML: {len(hrefs)}')

# Try fetching each CSS — look for 404 or error
for href in hrefs:
    try:
        rr = urllib.request.urlopen('http://127.0.0.1:8000' + href)
        print(f'  {rr.status} {href}  {len(rr.read())} bytes')
    except urllib.error.HTTPError as e:
        print(f'  {e.code} {href}  FAILED')
    except Exception as e:
        print(f'  ERR {href}  {e}')