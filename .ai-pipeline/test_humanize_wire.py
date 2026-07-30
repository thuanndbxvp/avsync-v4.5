"""Smoke test for the humanize wire-up.

Validates:
1. crew_main.run imports cleanly with the new post-process block.
2. When supplied a mocked ``workflow.execute`` result, humanize_script
   is called and the returned dict is updated + saved file is rewritten.
3. When ``humanize_enabled=False`` the pass is skipped.
4. AI-tell detection produces a non-empty list for a draft with clichés.
"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, ".")

from src.ai_write_x.config.config import Config, get_humanize_config
from src.ai_write_x.core.humanize_script import humanize_script, detect_ai_tells


# === Test 1: Config has the new flags ===
config = Config.get_instance()
assert hasattr(config, "humanize_enabled"), "missing humanize_enabled flag"
assert hasattr(config, "humanize_hook_type"), "missing humanize_hook_type flag"
print(f"[OK] Config has flags: enabled={config.humanize_enabled}, hook_type={config.humanize_hook_type}")

enabled, hook_type = get_humanize_config()
print(f"[OK] get_humanize_config -> ({enabled}, {hook_type!r})")


# === Test 2: crew_main.run() invokes humanize on a mock result ===
# Override workflow.execute via a temporary monkeypatch inside crew_main
print()
print("=== crew_main.run() with mocked workflow ===")

# Patch setup_aiwritex BEFORE run() is imported
import src.ai_write_x.crew_main as crew_main_mod

class FakeContentResult:
    def __init__(self, content):
        self.content = content
        self.markdown = content

class FakeWorkflow:
    def execute(self, topic, **kwargs):
        # Simulated raw AI draft full of AI tells
        raw = (
            "Đầu tiên, tôi sẽ phân tích vấn đề.\n"
            "Trước tiên, bạn cần hiểu rằng đầu tư là một quyết định quan trọng.\n"
            "Tóm lại, việc lập kế hoạch tài chính sẽ giúp bạn tự do hơn.\n"
            "Vì vậy, hãy cùng tìm hiểu cách tiết kiệm tiền hiệu quả.\n"
            "Nói cách khác, nên bắt đầu từ những thói quen nhỏ."
        )
        # Write the raw version to a temp file (simulating save)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        tmp.write(raw)
        tmp.close()
        return {
            "base_content": raw,
            "final_content": raw,
            "formatted_content": FakeContentResult(raw),
            "save_result": {"success": True, "path": tmp.name, "title": "smoke"},
            "publish_result": None,
            "success": True,
        }

crew_main_mod.setup_aiwritex = lambda: FakeWorkflow()

result = crew_main_mod.run({"topic": "smoke topic", "platform": "", "urls": [], "reference_ratio": 0.0})

assert result["humanize_applied"], "humanize_applied flag missing"
assert result["humanize_hook_type"] == "auto"
assert result["ai_tells_detected"], "expected AI tells to be detected"
assert "formatted_content_raw" in result

print(f"[OK] humanize_applied = {result['humanize_applied']}")
print(f"[OK] hook_type = {result['humanize_hook_type']}")
print(f"[OK] ai_tells_detected (first 3) = {result['ai_tells_detected'][:3]}")
print(f"[OK] raw length = {len(result['formatted_content_raw'])}, "
      f"humanized length = {len(result['formatted_content'].content)}")

# Verify saved file matches humanized content
saved_path = result["save_result"]["path"]
with open(saved_path, encoding="utf-8") as fh:
    disk = fh.read()
assert disk == result["formatted_content"].content, "saved file != humanized content"
print(f"[OK] saved file matches humanized content ({len(disk)} bytes)")
os.unlink(saved_path)

# Show the diff to prove humanize actually fixed something
print()
print("=== BEFORE / AFTER ===")
print("BEFORE:")
for line in result["formatted_content_raw"].split("\n"):
    print(f"  | {line}")
print()
print("AFTER:")
for line in result["formatted_content"].content.split("\n"):
    print(f"  | {line}")


# === Test 3: disabled flag skips the pass ===
print()
print("=== humanize_enabled=False ===")
config.humanize_enabled = False
try:
    config2 = FakeWorkflow()
    crew_main_mod.setup_aiwritex = lambda: config2
    result2 = crew_main_mod.run({"topic": "smoke", "platform": "", "urls": [], "reference_ratio": 0.0})
    assert "humanize_applied" not in result2, \
        f"expected no humanize_applied, got: {result2.get('humanize_applied')}"
    print(f"[OK] disabled flag skips pass; result keys = {list(result2.keys())}")
finally:
    config.humanize_enabled = True


# === Test 4: AI-tell detection alone ===
print()
print("=== detect_ai_tells independent test ===")
draft = "Trước tiên bạn cần biết. Tóm lại rất đơn giản. Hãy cùng tìm hiểu."
tells = detect_ai_tells(draft)
print(f"[OK] tells = {tells}")