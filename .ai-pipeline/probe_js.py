import urllib.request
# Fetch main.js as the browser would, and check its first 500 bytes
r = urllib.request.urlopen('http://127.0.0.1:8000/static/js/main.js')
body = r.read().decode('utf-8')
print('main.js length:', len(body))
print('---first 600 bytes---')
print(body[:600])
print('---last 400 bytes---')
print(body[-400:])
print('---contains DOMContentLoaded?', 'DOMContentLoaded' in body)
print('---contains showView?', 'showView' in body)
print('---contains view-content?', 'view-content' in body)