# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 7)

## QUYẾT ĐỊNH CỦA PLANNER
Tầng 2 phân tích rất chính xác! Ở Phase 6, Worker đang đóng vai trò POC với một biến `AiPrompter` giả định. Vì file `ai_prompts.py` chỉ chứa function (ví dụ: `generate_prompts(...)`) chứ không có class, POC hiện tại báo lỗi "Không tìm thấy module" và an toàn dừng lại.
Theo đề xuất, Phase 7 sẽ tiến hành **Wire (Đấu nối) Thật** cho tính năng Tạo Prompt.

## MỤC TIÊU CỦA PHASE 7
Tái thiết kế `core/worker_prompt.py` để sử dụng đúng hệ sinh thái hàm có sẵn của `app_legacy.py`:
1. `auto_edit.parse_srt` (Phân tích phụ đề)
2. `build_scenes.group_scenes` (Gom nhóm các đoạn SRT thành cảnh)
3. `ai_prompts.generate_prompts` (Gọi API tạo prompt dựa trên cảnh)

## LUỒNG HOẠT ĐỘNG
- Thay thế hoàn toàn cơ chế `AiPrompter`.
- Khi Worker chạy, nó sẽ đọc SRT thực tế mà người dùng truyền từ giao diện PySide6, phân tách ra các `texts`, sau đó nạp chung với `API Key`, `Model`, `Style` để truyền vào `ai_prompts.generate_prompts`.
- Các bước tiến độ sẽ được QThread emit ngược lên Console UI bằng `log_signal`.

## CÁC FILE CẦN CAN THIỆP
- `core/worker_prompt.py` (Viết lại logic hàm `run`)
