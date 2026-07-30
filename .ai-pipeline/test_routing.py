import sys
sys.path.insert(0, ".")
from src.ai_write_x.niches.router import HybridRouter

hr = HybridRouter(niche_id="finance-vn")
cases = [
    "7 thói quen tài chính của người 30 tuổi",
    "Top 5 cách tiết kiệm tiền hiệu quả",
    "Vì sao giới trẻ ngày càng khó mua nhà",
    "Làm gì khi bị áp lực đồng trang lứa",
    "Trả góp hay mua đứt xe ô tô",
    "Sự thật về tiền ảo",
    "Tại sao người giàu hay mua vàng",
    "3 nghề ngân hàng đang biến mất",
]
for t in cases:
    r = hr.route(t)
    print(f"{t:50s} -> {r.branch.value:12s} / {r.hook_type.value:8s} conf={r.confidence:.0%} source={r.source:18s} rule={r.matched_rule_id}")