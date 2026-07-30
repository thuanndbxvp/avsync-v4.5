# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 6)

## QUYẾT ĐỊNH CỦA PLANNER (Phản hồi AUDIT-REPORT)
Tầng 2 phát hiện lỗi cực kỳ sắc bén! Đúng là `ai_prompts.py` không có class `AiPrompter` mà là các function rời rạc như `generate_prompts()`, `generate_motion_prompts()`. 
Tôi đã thiết kế lại luồng Tích hợp (Integration) để gọi chính xác hệ sinh thái hàm có sẵn của `app_legacy.py` (bao gồm `auto_edit.parse_srt` và `build_scenes.group_scenes`).

## MỤC TIÊU CỦA PLANNER
Bắt đầu chiến dịch **Tích hợp Backend** (Logic Integration). 
Phase 6 sẽ thực hiện **POC (Proof of Concept) Tích hợp cho Tab Tạo Prompt** bằng cách tái sử dụng 100% logic từ `app_legacy.py` nhưng bọc trong một `QThread` để không làm đơ giao diện PySide6.

## CHIẾN LƯỢC TÍCH HỢP (DECOUPLING STRATEGY)
1. **Tạo lớp trung gian:** Tạo `core/worker_prompt.py` chứa `PromptWorker(QThread)`. Lớp này sẽ nhận Data Dictionary (chứa đường dẫn SRT, config, type...) từ giao diện PySide6.
2. **Kế thừa logic cũ:** Bóc tách logic của hàm `_make_prompts_thread` (trong `app_legacy.py`). Worker sẽ gọi `auto_edit.parse_srt`, sau đó gọi `build_scenes.group_scenes`, và cuối cùng gọi `ai_prompts.generate_prompts`.
3. **Kết nối Console:** Đẩy Signal log từ Worker lên thẳng `ConsoleLog` của `MainWindow`.

## CÁC FILE CẦN CAN THIỆP
- `core/worker_prompt.py` (Tạo mới: Xử lý ngầm tạo Prompt gọi hàm chuẩn xác)
- `ui/tabs/tab_prompt.py` (Cập nhật: Thu thập dữ liệu từ Form, gọi QThread)
- `ui/main_window.py` (Mở API cho phép các Tab in log xuống Console)
