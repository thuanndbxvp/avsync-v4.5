import urllib.request, urllib.error
paths = [
    '/static/css/main.css',
    '/static/css/views/article-manager.css',
    '/static/css/themes/light-theme.css',
    '/static/css/components/header.css',
    '/static/css/components/sidebar.css',
    '/static/css/components/footer.css',
    '/static/css/components/navigation.css',
    '/static/css/components/buttons.css',
    '/static/css/components/forms.css',
    '/static/css/components/notifications.css',
    '/static/css/components/modals.css',
    '/static/css/components/content-editor.css',
    '/static/css/views/shared-manager.css',
    '/static/css/views/creative-workshop.css',
    '/static/css/views/config-manager.css',
    '/static/js/main.js',
    '/static/js/article-manager.js',
    '/static/js/dialog.js',
    '/static/js/markdown-renderer.js',
    '/static/lib/marked/marked.min.js',
    '/static/lib/monaco/vs/loader.js',
]
for p in paths:
    try:
        r = urllib.request.urlopen('http://127.0.0.1:8000' + p)
        ct = r.headers.get('content-type', '-')
        body = r.read()
        print(f'{r.status} {ct:35} {p}  len={len(body)}')
    except urllib.error.HTTPError as e:
        print(f'{e.code}                                  {p}')
    except Exception as e:
        print(f'ERR                                {p}  {e}')