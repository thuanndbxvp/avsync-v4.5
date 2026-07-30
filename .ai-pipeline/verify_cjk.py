import urllib.request, urllib.error
# Fetch the main page and check for any remaining CJK
try:
    with urllib.request.urlopen('http://localhost:8000/') as r:
        body = r.read().decode('utf-8')
    print(f'Page length: {len(body)}')
    # Count CJK characters in the served HTML
    cjk_count = sum(1 for c in body if '一' <= c <= '鿿')
    print(f'CJK chars in served HTML: {cjk_count}')
    # Sample any CJK still present
    import re
    cjk_runs = re.findall(r'[一-鿿]+', body)
    if cjk_runs:
        print('Remaining CJK runs (sample):')
        for r in cjk_runs[:20]:
            print(f'  {r!r}')
except Exception as e:
    print(f'Error: {e}')