"""Try to parse every served CSS file. If the browser sees an early syntax
error, the rest of the cascade is silently dropped, which matches what the
screenshot shows (no styling at all).
"""
import urllib.request, re

paths = [
    '/static/css/main.css',
    '/static/css/themes/light-theme.css',
    '/static/css/themes/dark-theme.css',
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
    '/static/css/views/article-manager.css',
    '/static/css/views/config-manager.css',
]

# Naive balanced-brace check
def balance_check(text):
    """Walk through and report unmatched braces.
    We skip chars inside string literals and comments to avoid false positives.
    """
    i = 0
    depth = 0
    in_str = None
    in_comment = False
    while i < len(text):
        c = text[i]
        nxt = text[i+1] if i+1 < len(text) else ''
        if in_comment:
            if c == '*' and nxt == '/':
                in_comment = False
                i += 2
                continue
        elif in_str:
            if c == '\\':
                i += 2
                continue
            if c == in_str:
                in_str = None
        else:
            if c == '/' and nxt == '*':
                in_comment = True
                i += 2
                continue
            if c == '"' or c == "'":
                in_str = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth < 0:
                    return f"unmatched }} at offset {i}"
        i += 1
    if depth != 0:
        return f"unclosed braces, depth={depth}"
    return "ok"

for p in paths:
    req = urllib.request.Request('http://127.0.0.1:8000' + p, headers={'Accept-Language': 'vi-VN'})
    r = urllib.request.urlopen(req)
    body = r.read().decode('utf-8')
    result = balance_check(body)
    flag = '' if result == 'ok' else f'  <-- {result}'
    print(f'{p}  len={len(body)}{flag}')