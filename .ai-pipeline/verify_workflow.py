"""End-to-end verification: DNA loader + 152 routing + 1 generation + constraints."""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(url, body):
    req = urllib.request.Request(
        f"{BASE}{url}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))


def get(url):
    return json.loads(urllib.request.urlopen(f"{BASE}{url}", timeout=10).read().decode("utf-8"))


# 1. DNA loader
print("=== [1] DNA loader ===")
profile = get("/api/niche/profile")
print(f"  brand: {profile['metadata']['primary_brand']}")
print(f"  branches: {profile['branches']}")
print(f"  routing_rules: {len(profile['routing_rules'])} rules")
print(f"  constraints: {len(profile['constraints'])} rules")
print(f"  hooks: {len(profile['hooks'])} hooks")

# 2. Route all 152 titles
print("\n=== [2] Route 152 titles ===")
all_topics = get("/api/topics?limit=200")
assert all_topics["total"] >= 152, f"Expected >=152 topics, got {all_topics['total']}"

# Re-fetch full 152
all_topics_full = get("/api/topics?limit=200")
total = all_topics_full["total"]
items = all_topics_full["items"]
print(f"  total: {total}")

branch_counts = {}
hook_distribution = {}
fail = []
for t in items:
    try:
        res = post("/api/niche/route", {"title": t["title"]})
        b = res["decision"]["branch"]
        h = res["decision"]["hook_priority"][0]
        branch_counts[b] = branch_counts.get(b, 0) + 1
        hook_distribution[h] = hook_distribution.get(h, 0) + 1
    except Exception as e:
        fail.append((t["id"], str(e)))

print(f"  routed: {total - len(fail)}/{total}")
print(f"  branch distribution: {branch_counts}")
print(f"  hook distribution:   {hook_distribution}")
if fail:
    print(f"  FAIL: {fail[:3]}")

assert len(fail) == 0, "Some titles failed routing"
assert len(branch_counts) >= 3, f"Only {len(branch_counts)} branches hit (expect 3+)"

# 3. Generate 1 script-style prompt
print("\n=== [3] Generate 1 finance script prompt ===")
topic = "7 Thứ Người Giàu Không Bao Giờ Mua"
res = post("/api/generate/finance", {
    "title": topic,
    "audience": "Người đi làm 25-35 tuổi, lương 15-25 triệu",
    "word_count": 3000,
})
print(f"  title: {topic}")
print(f"  branch: {res['branch']}")
print(f"  hook_type: {res['hook_type']}")
print(f"  prompt length: {len(res['prompt'])} chars")

required_sections = ["## CORE DNA", "## BRANCH DNA", "## HOOK",
                     "## HARD CONSTRAINTS", "## INPUT", "## OUTPUT FORMAT"]
missing = [s for s in required_sections if s not in res["prompt"]]
print(f"  missing sections: {missing or 'none'}")
assert not missing, f"Missing: {missing}"
print(f"  ✓ all 6 sections present")

# 4. Constraint validation
print("\n=== [4] Constraint validation ===")
sample_script = """
Xin chào anh em, tôi là Chú Quế Tài Chính. Hôm nay tôi kể câu chuyện của Minh, 28 tuổi, 
nhân viên văn phòng tại Hà Nội với mức lương 15 triệu (theo khảo sát của Navigos Group 2024, 
mức lương trung bình ngành IT tại Hà Nội khoảng 18-25 triệu). Minh đã tiết kiệm được 50 triệu 
trong vòng 2 năm theo quy tắc 50/30/20. Theo thống kê của ngân hàng thế giới 2024, 
tỷ lệ tiết kiệm trung bình của người Việt là 15% thu nhập. Minh áp dụng nguyên tắc 
pay yourself first - trích 20% lương ngay khi nhận (ước tính khoảng 3 triệu/tháng), trước khi 
chi tiêu bất kỳ khoản nào. Mời anh em thử xem có phù hợp không. Hẹn gặp lại.

Disclaimer: video chỉ mang tính chia sẻ kinh nghiệm cá nhân, không phải lời khuyên đầu tư.
"""

res = post("/api/niche/validate", {"script": sample_script, "topic": topic})
print(f"  passed: {res['passed']}")
print(f"  results: {len(res['results'])} rules evaluated")
for r in res["results"]:
    status = "✓" if r["passed"] else "✗"
    print(f"    {status} {r['rule_id']}: {r['reason'][:60]}")
    if "injected" in r and r.get("injected"):
        print(f"      → injected: {r.get('injected_text', '')[:80]}")

print("\n=== Summary ===")
print(f"  DNA loaded:    {len(profile['routing_rules'])} routing + {len(profile['constraints'])} constraints")
print(f"  topics routed: {total}/{total}")
print(f"  prompt OK:     {len(res['results'])}/7 constraints evaluated")
print(f"  ALL GREEN ✓" if res["passed"] else "  Script needs fix")