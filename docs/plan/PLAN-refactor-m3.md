# KIẾN TRÚC TỔNG QUAN: CORE REFACTORING (MILESTONE 3)

## MỤC TIÊU CỦA PLANNER
Milestone 3 (M3) nhằm giải quyết thảm họa "God Function" `render_video()` trong `auto_edit.py`. Hiện tại, hàm này dài 400 dòng và gọi FFMPEG lắt nhắt hàng chục lần. 
Mục tiêu là gom nhóm các lệnh FFMPEG bằng `filter_complex` (Batching) để giảm thiểu Overhead khi khởi tạo Process, qua đó tăng tốc toàn bộ quá trình render lên tới 4 lần.

## NHIỆM VỤ CỐT LÕI
1. **FFMPEG Client (`infrastructure/ffmpeg_client.py`)**:
   - Mở rộng FFMPEG Client, xây dựng hàm `build_master_clip` để nối (concat) N cảnh lại trong 1 lệnh duy nhất thông qua chuỗi `-filter_complex`.
2. **Render Service (`services/render_service.py`)**:
   - Bóc tách hàm `render_video()` cũ, viết lại luồng xử lý: Plan -> Gather Clips -> Master Concat.
3. **Re-export (`auto_edit.py`)**:
   - Thay ruột hàm `render_video()` cũ bằng việc gọi `render_service.render()`. Giữ nguyên đầu vào/đầu ra để CLI không bị hỏng.

## CÁC FILE CẦN CAN THIỆP
- Thêm/Sửa: `infrastructure/ffmpeg_client.py`, `services/render_service.py`
- Sửa đổi: `auto_edit.py`
