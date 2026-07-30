import urllib.request, re

req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Language': 'vi-VN,vi;q=0.9'})
r = urllib.request.urlopen(req)
html = r.read().decode('utf-8')

# Check for important elements
checks = {
    'has <link main.css>': '/static/css/main.css' in html,
    'has <link light-theme.css>': '/static/css/themes/light-theme.css' in html,
    'has <link dark-theme.css>': '/static/css/themes/dark-theme.css' in html,
    'has <link header.css>': '/static/css/components/header.css' in html,
    'has <link sidebar.css>': '/static/css/components/sidebar.css' in html,
    'has <script main.js>': '/static/js/main.js' in html,
    'has #creative-workshop-view': 'id="creative-workshop-view"' in html,
    'has #article-manager-view': 'id="article-manager-view"' in html,
    'has #config-manager-view': 'id="config-manager-view"' in html,
    'has app-container div': 'class="app-container"' in html,
    'has app-main div': 'class="app-main"' in html,
    'has window-mode body class': 'window-mode-standard' in html,
    'HTML lang attr': '<html lang="vi">' in html,
}
for k, v in checks.items():
    print(f'{"OK" if v else "NO":3}  {k}')

# Check inline scripts that run before main.js
print('\n--- inline scripts (between </head> and <script src=main.js>) ---')
m = re.search(r'</head>(.*?)<script src="/static/js/main.js"', html, re.DOTALL)
if m:
    print('Has inline block before main.js:', len(m.group(1)), 'bytes')

# What stylesheets load?
print('\n--- stylesheet links ---')
for m in re.finditer(r'<link rel="stylesheet" href="([^"]+)"', html):
    print(' ', m.group(1))