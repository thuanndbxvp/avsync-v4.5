# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 5)

## MỤC TIÊU CỦA PLANNER
Hoàn thiện mảnh ghép giao diện cuối cùng: **Tab Cài đặt**.
Tab này quản lý các thiết lập cốt lõi của ứng dụng, từ API Key (AI) cho đến các phong cách (Style Profiles) dùng chung cho mọi video. Giao diện được thiết kế hiện đại, bám sát bản thiết kế Tailwind `screen4_cai_dat.html`.

## LUỒNG DỮ LIỆU VÀ GIAO DIỆN
- **Section 1 (Cấu hình hệ thống):** Phiên bản, ngôn ngữ.
- **Section 2 (API Prompt):** Quản lý nhà cung cấp (Gemini/OpenAI), Model, và trường nhập API Key ẩn (có nút hiển thị password).
- **Section 3 (Style Visual Profile):** Giao diện chia 2 cột:
  - Cột trái: `QListWidget` hiển thị tên các Profile (Người que, Tâm linh, v.v.).
  - Cột phải: `QTextEdit` hiển thị nội dung prompt chi tiết của Profile đang chọn.
- Các nút lưu, kiểm tra kết nối, xoá, thêm profile tạm thời sử dụng MessageBox (sẽ đấu nối thật ở Phase 6).

## CÁC FILE CẦN CAN THIỆP
- `ui/tabs/tab_settings.py` (Tạo mới)
- `ui/main_window.py` (Cập nhật để thay thế Tab giữ chỗ cuối cùng bằng `SettingsTab`)
- `ui/style.qss` (Bổ sung phong cách cho ListWidget và TextEdit trong phần Profile)
