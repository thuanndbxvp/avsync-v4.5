"""Compare on-disk vs served file. Catch any corruption the middleware
introduces that might break CSS syntax in the browser.
"""
import urllib.request

files = [
    'src/ai_write_x/web/static/css/main.css',
    'src/ai_write_x/web/static/css/themes/light-theme.css',
    'src/ai_write_x/web/static/css/components/header.css',
    'src/ai_write_x/web/static/css/views/creative-workshop.css',
    'src/ai_write_x/web/static/css/components/buttons.css',
]

for rel in files:
    disk = open(rel, 'rb').read()
    req = urllib.request.Request(
        'http://127.0.0.1:8000/static/' + rel.split('static/')[-1].replace('\\', '/'),
        headers={'Accept-Language': 'vi-VN,vi;q=0.9'},
    )
    r = urllib.request.urlopen(req)
    served = r.read()
    print('=' * 80)
    print(f'{rel}')
    print(f'disk={len(disk)}  served={len(served)}  equal={disk == served}')
    if disk != served:
        # Show first divergence
        for i in range(min(len(disk), len(served))):
            if disk[i] != served[i]:
                ctx_disk = disk[max(0,i-20):i+40].decode('utf-8', errors='replace')
                ctx_serv = served[max(0,i-20):i+40].decode('utf-8', errors='replace')
                print(f'first diff at byte {i}:')
                print(f'  disk:  ...{ctx_disk}...')
                print(f'  serv:  ...{ctx_serv}...')
                break