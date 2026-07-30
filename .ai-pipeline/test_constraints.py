"""Smoke-test constraints validator with positive + negative cases."""
from src.ai_write_x.niches.constraints import validate, validate_or_inject


print("=== Test 1: clean script (should PASS all 7) ===")
clean = """Chào mừng anh em đến với Chú Que Tài Chính.
Hôm nay tôi kể câu chuyện về Minh, 28 tuổi, lương 15 triệu.
Minh tiết kiệm được 50 triệu trong 2 năm.
Bí quyết: theo kinh nghiệm, Minh áp dụng quy tắc 50/30/20.
Anh em thử xem có phù hợp không.
Tiền bạc không phải là đích đến, mà là phương tiện để anh em sống được cuộc đời mình muốn.
"""
r = validate(clean, topic="Quản lý tài chính cá nhân")
print(f"  passed: {r.passed}")
for x in r.results:
    print(f"    {x.rule_id}: {'PASS' if x.passed else 'FAIL ' + x.reason}")
print()

print("=== Test 2: fakes numbers (should FAIL no-fake-numbers) ===")
fake = """Tôi cam đoan đầu tư 100 triệu sẽ được 20 triệu sau 1 năm.
Không cần làm gì cả, chỉ cần đợi."""
r = validate(fake, topic="Đầu tư")
print(f"  passed: {r.passed}")
for x in r.failures:
    print(f"    FAIL {x.rule_id}: {x.reason}")
print()

print("=== Test 3: moralize (should FAIL no-moralize) ===")
bad_moral = """Anh em phải tỉnh táo lên đi.
Đừng có mơ mộng nữa."""
r = validate(bad_moral, topic="Khủng hoảng")
print(f"  passed: {r.passed}")
for x in r.failures:
    print(f"    FAIL {x.rule_id}: {x.reason}")
print()

print("=== Test 4: investment topic without disclaimer (should FAIL investment-disclaimer) ===")
inv_script = """Tôi sẽ nói về cổ phiếu VN30 và cách chọn.
Đầu tư chứng khoán cần lưu ý rủi ro."""
r = validate(inv_script, topic="Cổ phiếu VN30")
print(f"  passed: {r.passed}")
for x in r.failures:
    print(f"    FAIL {x.rule_id}: {x.reason}")

print()
print("=== Test 5: investment topic + auto-inject disclaimer (should PASS) ===")
r = validate_or_inject(inv_script, topic="Cổ phiếu VN30")
print(f"  passed: {r.passed}")
print(f"  injected_disclaimer (first 80 chars): {r.injected_disclaimer[:80] if r.injected_disclaimer else 'None'!r}")
print()

print("=== Test 6: borrow-to-invest (should FAIL) ===")
borrow = """Anh em nên vay tiền ngân hàng để đầu tư cổ phiếu."""
r = validate(borrow, topic="Đầu tư cổ phiếu")
print(f"  passed: {r.passed}")
for x in r.failures:
    print(f"    FAIL {x.rule_id}: {x.reason}")
print()

print("=== Test 7: discrimination (should FAIL) ===")
disc = """Miền Bắc thì tệ hơn miền Nam trong kinh doanh."""
r = validate(disc, topic="Kinh doanh")
print(f"  passed: {r.passed}")
for x in r.failures:
    print(f"    FAIL {x.rule_id}: {x.reason}")