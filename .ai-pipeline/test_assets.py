"""Verify all JS files referenced by index.html are accessible."""
import urllib.request

JS_FILES = [
    "/static/lib/marked/marked.min.js",
    "/static/js/markdown-renderer.js",
    "/static/lib/monaco/vs/loader.js",
    "/static/js/dialog.js",
    "/static/js/main.js",
    "/static/js/progress-manager.js",
    "/static/js/creative-workshop.js",
    "/static/js/article-manager.js",
    "/static/js/config-manager.js",
    "/static/js/theme-manager.js",
    "/static/js/window-modes.js",
]

CSS_FILES = [
    "/static/css/main.css",
    "/static/css/themes/light-theme.css",
    "/static/css/themes/dark-theme.css",
    "/static/css/components/header.css",
    "/static/css/components/sidebar.css",
    "/static/css/components/footer.css",
    "/static/css/components/navigation.css",
    "/static/css/components/buttons.css",
    "/static/css/components/forms.css",
    "/static/css/components/notifications.css",
    "/static/css/components/modals.css",
    "/static/css/components/content-editor.css",
    "/static/css/views/shared-manager.css",
    "/static/css/views/creative-workshop.css",
    "/static/css/views/article-manager.css",
    "/static/css/views/config-manager.css",
]

print("=== JS files ===")
for path in JS_FILES:
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=5)
        size = len(r.read())
        print(f"  {r.status} {size:>8} chars  {path}")
    except Exception as e:
        print(f"  ERR  {path}: {e}")

print("\n=== CSS files ===")
for path in CSS_FILES:
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=5)
        size = len(r.read())
        print(f"  {r.status} {size:>8} chars  {path}")
    except Exception as e:
        print(f"  ERR  {path}: {e}")

# Removed files should 404
print("\n=== Removed files (should be 404 or unused) ===")
for path in [
    "/static/js/preview-panel.js",
    "/static/js/update-checker.js",
    "/static/js/footer-marquee.js",
    "/static/js/template-manager.js",
    "/static/js/content-editor.js",
    "/static/js/image-designer.js",
    "/static/lib/grapesjs/grapes.min.js",
]:
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=5)
        print(f"  STILL EXISTS (404 not expected if file present but unused): {path}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  404 (good - cleaned up): {path}")
        else:
            print(f"  {e.code}: {path}")