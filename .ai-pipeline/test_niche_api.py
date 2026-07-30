"""Test all niche API endpoints."""
import urllib.request
import json


def fetch(url, method="GET", body=None):
    if method == "GET":
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=10)
    return json.loads(r.read().decode("utf-8"))


BASE = "http://127.0.0.1:8000"

print("=== GET /api/niche/profile ===")
data = fetch(f"{BASE}/api/niche/profile")
print("  metadata.brand:", repr(data["metadata"]["primary_brand"]))
print("  branches:", data["branches"])
print("  routing_rules:", len(data["routing_rules"]), "rules")
print("  constraints:", len(data["constraints"]), "rules")

print()
print("=== GET /api/topics?limit=3 ===")
data = fetch(f"{BASE}/api/topics?limit=3")
print("  total:", data["total"])
for t in data["items"]:
    print("   ", t["id"], t["branch"], t["title"][:60])

print()
print("=== GET /api/topics?branch=listicle&limit=3 ===")
data = fetch(f"{BASE}/api/topics?branch=listicle&limit=3")
print("  total:", data["total"])
for t in data["items"]:
    print("   ", t["id"], t["branch"], t["title"][:60])

print()
print("=== GET /api/topics?q=Bitcoin ===")
data = fetch(f"{BASE}/api/topics?q=Bitcoin")
print("  total:", data["total"])
for t in data["items"]:
    print("   ", t["id"], t["branch"], t["title"][:60])

print()
print("=== POST /api/niche/route ===")
data = fetch(f"{BASE}/api/niche/route", method="POST",
             body={"title": "7 Thứ Người Giàu Không Bao Giờ Mua"})
print("  branch:", data["decision"]["branch"])
print("  hook_priority:", data["decision"]["hook_priority"])
print("  matched_rule:", data["decision"]["matched_rule"])

print()
print("=== POST /api/niche/route with overrides ===")
data = fetch(f"{BASE}/api/niche/route", method="POST",
             body={"title": "Test title", "branch_override": "psychology", "hook_override": "data"})
print("  branch:", data["decision"]["branch"])
print("  hook_priority:", data["decision"]["hook_priority"])

print()
print("=== POST /api/generate/finance ===")
data = fetch(f"{BASE}/api/generate/finance", method="POST",
             body={"title": "5 Cach Dung Tien Luong Thong Minh Hon",
                   "audience": "Nguoi di lam 25-35 tuoi",
                   "word_count": 3000})
print("  branch:", data["branch"])
print("  hook_type:", data["hook_type"])
print("  prompt length:", len(data["prompt"]), "chars")
print("  has CORE:", "## CORE DNA" in data["prompt"])
print("  has BRANCH:", "## BRANCH DNA" in data["prompt"])
print("  has HOOK:", "## HOOK" in data["prompt"])
print("  has CONSTRAINTS:", "## HARD CONSTRAINTS" in data["prompt"])
print("  has INPUT:", "## INPUT" in data["prompt"])
print("  has OUTPUT:", "## OUTPUT FORMAT" in data["prompt"])

print()
print("=== POST /api/niche/validate (clean script) ===")
clean = (
    "Chao mung anh em den voi Chu Que Tai Chinh. "
    "Hom nay toi ke ve Minh, 28 tuoi. Minh tiet kiem 50 trieu trong 2 nam. "
    "Theo kinh nghiem, Minh ap dung quy tac 50/30/20. "
    "Anh em thu xem co phu hop khong. "
    "Disclaimer: video chi mang tinh chia se, khong phai loi khuyen dau tu."
)
data = fetch(f"{BASE}/api/niche/validate", method="POST",
             body={"script": clean, "topic": "Quan ly tai chinh"})
print("  passed:", data["passed"])

print()
print("=== POST /api/niche/validate (bad script) ===")
bad = "Hung vay 100 trieu de mua co phieu, chac chan loi 50%."
data = fetch(f"{BASE}/api/niche/validate", method="POST",
             body={"script": bad, "topic": "Co phieu"})
print("  passed:", data["passed"])
print("  injected_disclaimer present:", bool(data.get("injected_disclaimer")))
for res in data["results"]:
    if not res["passed"]:
        print("    FAIL", res["rule_id"], res["reason"][:80])