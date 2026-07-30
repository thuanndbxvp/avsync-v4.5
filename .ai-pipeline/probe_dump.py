"""Fetch /, dump to file, then read back via PowerShell Get-Content."""
import urllib.request

for accept, fname in [("vi", "vi.html"), ("en", "en.html"), (None, "no.html")]:
    req = urllib.request.Request("http://127.0.0.1:8000/")
    if accept:
        req.add_header("Accept-Language", accept)
    r = urllib.request.urlopen(req, timeout=5)
    body = r.read()
    with open(f".ai-pipeline/probe_{fname}", "wb") as f:
        f.write(body)
    # Also dump UTF-8 decoded to text file so PowerShell displays correctly
    with open(f".ai-pipeline/probe_{fname}.txt", "w", encoding="utf-8") as f:
        f.write(body.decode("utf-8", errors="replace"))
    print(f"  wrote probe_{fname} ({len(body)} bytes)")

# Print a clean summary to stdout
import os
for fname in ["no.html", "vi.html", "en.html"]:
    p = f".ai-pipeline/probe_{fname}.txt"
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            body = f.read()
        # Count chars properly
        cjk = sum(1 for c in body if '一' <= c <= '鿿')
        vi = sum(1 for c in body if 'à' <= c <= 'ỹ')
        # Pull title
        title = body[body.find('<title>'):body.find('</title>')+8] if '<title>' in body else 'N/A'
        print(f"  {fname:8s} len={len(body):6d} cjk={cjk:5d} vi={vi:5d} title={title!r}")