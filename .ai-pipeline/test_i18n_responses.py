"""Verify i18n middleware translates HTML and JS files."""
import urllib.request
import re

for accept in ['vi', 'en', None]:
    print(f"=== Accept-Language: {accept!r} ===")
    for path in ['/', '/static/js/dialog.js', '/static/js/main.js']:
        req = urllib.request.Request(f'http://127.0.0.1:8000{path}')
        if accept:
            req.add_header('Accept-Language', accept)
        try:
            r = urllib.request.urlopen(req, timeout=5)
            body = r.read().decode('utf-8', errors='replace')
            cjk = sum(1 for c in body if '一' <= c <= '鿿')
            vi = sum(1 for c in body if 'à' <= c <= 'ỹ')
            print(f'  {path:50s} status={r.status} len={len(body):6d} cjk={cjk:5d} vi={vi:5d}')
        except Exception as e:
            print(f'  {path}: ERR {e}')

print()
print('=== Sample Vietnamese strings in dialog.js ===')
req = urllib.request.Request('http://127.0.0.1:8000/static/js/dialog.js')
req.add_header('Accept-Language', 'vi')
body = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='replace')
matches = re.findall(r'["\u0027]([^"\u0027]{4,50})["\u0027]', body)
vietnamese_strs = [m for m in matches if any('à' <= c <= 'ỹ' for c in m)]
print(f'  total VN strings: {len(vietnamese_strs)}')
for s in vietnamese_strs[:10]:
    print(f'    - {s!r}')