import urllib.request

paths = [
    '/static/css/main.css',
    '/static/css/components/header.css',
    '/static/css/views/creative-workshop.css',
    '/static/css/themes/light-theme.css',
]

for p in paths:
    req = urllib.request.Request('http://127.0.0.1:8000' + p, headers={
        'Accept-Language': 'vi-VN,vi;q=0.9',
        'Accept': 'text/css,*/*;q=0.1',
    })
    r = urllib.request.urlopen(req)
    body = r.read().decode('utf-8')
    print('=' * 80)
    print(f'{p}  len={len(body)}')
    print('--- first 600 bytes ---')
    print(body[:600])
    print('--- contains chinese?', any('\u4e00' <= c <= '\u9fff' for c in body))