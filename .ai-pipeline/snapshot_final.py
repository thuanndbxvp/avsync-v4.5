"""Save current rendered HTML for visual inspection."""
import urllib.request

req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "vi")
body = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")

with open(".ai-pipeline/probe_vi_final.html", "w", encoding="utf-8") as f:
    f.write(body)

# Show the workshop header area
import re
m = re.search(r'<div class="workshop-header">.*?</div>\s*</div>', body, re.DOTALL)
if m:
    print("=== WORKSHOP HEADER ===")
    snippet = m.group(0)
    # Strip SVG noise for readability
    snippet = re.sub(r'<svg.*?</svg>', '[SVG]', snippet, flags=re.DOTALL)
    snippet = re.sub(r'\s+', ' ', snippet)
    print(snippet[:600])

m = re.search(r'<header class="app-header">.*?</header>', body, re.DOTALL)
if m:
    print("\n=== APP HEADER ===")
    snippet = m.group(0)
    snippet = re.sub(r'<svg.*?</svg>', '[SVG]', snippet, flags=re.DOTALL)
    snippet = re.sub(r'\s+', ' ', snippet)
    print(snippet[:600])