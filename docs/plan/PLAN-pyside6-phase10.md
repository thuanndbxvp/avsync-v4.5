# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 10)

## MỤC TIÊU CỦA PLANNER
Tiếp tục chiến dịch "Wire thật" (Đấu nối logic thật) cho **Tab Video Ngủ**. Ở Phase 8, chúng ta đã dựng sẵn `core/worker_sleep.py` nhưng chỉ chạy hàm POC giả lập. Nhiệm vụ của Phase 10 là móc nối vào logic xử lý Video Ngủ thực tế của app cũ.

## NHIỆM VỤ CỐT LÕI
1. **Tìm & Tách logic Video Ngủ:** Khảo sát `app_legacy.py` (cụ thể là hàm `run_make_sleep` hoặc luồng thread của Video Ngủ). Bóc tách toàn bộ code FFmpeg/ghép ảnh dài đó ra thành một hàm độc lập `render_sleep_video(...)`.
2. **Nơi lưu trữ logic:** Đưa hàm `render_sleep_video(...)` vào file `core/sleep_video.py` (tạo mới) để code gọn gàng, hoặc nhét thẳng vào `auto_edit.py` tùy quyết định của Tầng 2. 
3. **Cập nhật `worker_sleep.py`:** Loại bỏ phần code POC, thay bằng việc gọi hàm thật vừa bóc tách.

## CÁC FILE CẦN CAN THIỆP
- `app_legacy.py` (Dùng để tham khảo và bóc tách logic Video Ngủ cũ)
- `core/sleep_video.py` (Tạo mới: Chứa top-level function `render_sleep_video`)
- `core/worker_sleep.py` (Cập nhật: Gọi hàm thật từ module `sleep_video`)
