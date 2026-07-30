"""Smoke-test prompt builder."""
from src.ai_write_x.niches.prompts import build_prompt

# Test 1: listicle title
print("=== Test 1: listicle (default routing) ===")
result = build_prompt(
    "7 Thứ Người Giàu Thực Sự Không Bao Giờ Mua",
    audience="Người đi làm 25-40 tuổi",
    word_count=3000,
)
print(f"  branch: {result['branch']}")
print(f"  hook_type: {result['hook_type']}")
print(f"  matched_rule: {result['matched_rule']}")
print(f"  prompt length: {len(result['prompt'])} chars")
print(f"  has CORE DNA: {'## CORE DNA' in result['prompt']}")
print(f"  has BRANCH DNA: {'## BRANCH DNA' in result['prompt']}")
print(f"  has HOOK section: {'## HOOK' in result['prompt']}")
print(f"  has CONSTRAINTS: {'## HARD CONSTRAINTS' in result['prompt']}")
print(f"  has INPUT: {'## INPUT' in result['prompt']}")
print(f"  has OUTPUT: {'## OUTPUT FORMAT' in result['prompt']}")
print()

# Test 2: explicit overrides
print("=== Test 2: branch_override='psychology', hook_override='question' ===")
result = build_prompt(
    "Làm Gì Khi Bạn Bè Đều Đã Giàu?",
    branch_override="psychology",
    hook_override="question",
)
print(f"  branch: {result['branch']}")
print(f"  hook_type: {result['hook_type']}")
print(f"  prompt length: {len(result['prompt'])} chars")
print()

# Test 3: investment topic (verify disclaimer is in OUTPUT format expectations)
print("=== Test 3: investment topic with outline ===")
result = build_prompt(
    "Có 500 Triệu Nên Đầu Tư Gì?",
    audience="Người 30-45 tuổi có tiết kiệm",
    outline="30 ngày chờ, trả nợ, quỹ 6-12 tháng, phân bổ theo mốc TG",
)
print(f"  branch: {result['branch']}")
print(f"  hook_type: {result['hook_type']}")
print(f"  prompt contains outline: {'30 ngày chờ' in result['prompt']}")
print()

# Print first 600 chars of the prompt for visual inspection
print("=== Sample prompt (first 800 chars) ===")
print(result["prompt"][:800])