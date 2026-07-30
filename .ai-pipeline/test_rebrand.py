"""Verify rebrand: check page title, header text, sidebar items, footer text."""
import urllib.request
import re

req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "vi")
r = urllib.request.urlopen(req, timeout=5)
body = r.read().decode("utf-8")

print("=== TITLE ===")
m = re.search(r"<title>([^<]+)</title>", body)
print(f"  {m.group(1) if m else 'NO TITLE'}")

print("\n=== HEADER ===")
for needle in ["Chú Quế Tài Chính", "Chuyên gia viết kịch bản tài chính cá nhân",
               "DNA Script Engine", "Sẵn sàng", "Taobao", "官方淘宝店", "智能内容创作平台"]:
    found = needle in body
    print(f"  {'YES' if found else 'no ':3} {needle!r}")

print("\n=== SIDEBAR ===")
for needle in ["Xưởng Kịch bản", "Kho bài viết", "Cài đặt", "Finance DNA",
               "nav-badge", "sidebar-brand-footer",
               "创意工坊", "文章管理", "模板管理", "系统设置"]:
    found = needle in body
    print(f"  {'YES' if found else 'no ':3} {needle!r}")

print("\n=== WORKSHOP ===")
for needle in ["Chú Quế Tài Chính", "Chọn chủ đề từ 152 ý tưởng tài chính",
               "Finance Niche", "finance-build-prompt-btn", "finance-generate-btn",
               "Bắt đầu tạo kịch bản", "Xây dựng Prompt"]:
    found = needle in body
    print(f"  {'YES' if found else 'no ':3} {needle!r}")

print("\n=== FOOTER ===")
for needle in ["Chú Quế Tài Chính · DNA Script Engine", "Multi-Agent",
               "AIWriteX CrewAI", "墨智工坊", "🔥爆款AI工具", "taobao"]:
    found = needle in body
    print(f"  {'YES' if found else 'no ':3} {needle!r}")

print("\n=== REMOVED ELEMENTS ===")
for needle in ["preview-panel", "update-checker", "footer-marquee",
               "taobao", "aiforge.taobao.com", "grapesjs", "image-designer",
               "template-manager", "Tiki", "shop-badge"]:
    found = needle in body
    print(f"  {'NO (good)' if not found else 'YES (BAD)' if needle in ['taobao', 'aiforge.taobao.com', '🔥爆款AI工具', 'Tiki', 'shop-badge'] else 'NO (good)'}  {needle!r}")