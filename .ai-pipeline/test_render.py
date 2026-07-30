"""Render-time check: count nav items, count panels, ensure finance-niche-panel rendered."""
import urllib.request
import re

req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "vi")
body = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")

# Count nav items in sidebar
nav_items = re.findall(r'<li class="nav-item[^"]*"', body)
print(f"nav-items in sidebar: {len(nav_items)}")

# Check Finance Niche panel state (should not have 'collapsed' class on the rendered panel — JS will toggle)
panel_idx = body.find("finance-niche-panel")
if panel_idx > 0:
    snippet = body[panel_idx:panel_idx + 200]
    has_collapsed = "collapsed" in snippet.split(">", 1)[0]
    print(f"finance-niche-panel present at offset {panel_idx}, starts collapsed? {has_collapsed}")

# Confirm all expected IDs in HTML
ids = ["creative-workshop-view", "article-manager-view", "config-manager-view",
       "finance-niche-panel", "finance-topic-select", "finance-build-prompt-btn",
       "finance-generate-btn", "finance-open-panel-btn", "topic-input",
       "generate-btn", "log-progress-btn"]
for _id in ids:
    needle = 'id="' + _id + '"'
    present = needle in body
    print(f"  {'YES' if present else 'NO '} #{_id}")

# Footer text
ft = re.search(r'<footer[^>]*>(.*?)</footer>', body, re.DOTALL)
if ft:
    txt = re.sub(r'<[^>]+>', '|', ft.group(1))
    txt = re.sub(r'\|+', ' | ', txt).strip()
    print(f"\nFOOTER text: {txt}")

# Sidebar brand footer
sb = re.search(r'sidebar-brand-footer.*?</div>\s*</div>\s*</aside>', body, re.DOTALL)
if sb:
    txt = re.sub(r'<[^>]+>', '|', sb.group(0))
    txt = re.sub(r'\|+', ' | ', txt).strip()
    print(f"\nSIDEBAR BRAND text: {txt[:200]}")