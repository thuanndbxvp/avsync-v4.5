import urllib.request

req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "vi")
r = urllib.request.urlopen(req, timeout=5)
body = r.read().decode("utf-8")

for tag in ("finance-niche-panel", "finance-branch-filter", "finance-topic-select",
            "finance-routed-branch", "finance-build-prompt-btn", "finance-prompt-output",
            "escapeHtml", "initFinanceNiche", "loadFinanceTopics", "buildFinancePrompt"):
    print(f"  {tag}: {'YES' if tag in body else 'no'}")

# Also verify JS endpoints are reachable
import json
for ep in ["/api/topics?limit=3", "/api/niche/profile"]:
    req = urllib.request.Request(f"http://127.0.0.1:8000{ep}")
    req.add_header("Accept-Language", "vi")
    r = urllib.request.urlopen(req, timeout=5)
    data = json.loads(r.read().decode("utf-8"))
    print(f"  {ep}: {r.status} → keys={list(data.keys()) if isinstance(data, dict) else type(data).__name__}")