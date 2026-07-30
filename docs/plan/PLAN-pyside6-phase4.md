# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 4)

## MỤC TIÊU CỦA PLANNER
Hoàn thiện song song 2 Tab: **Video Ngủ** và **Hàng Đợi**.
- **Tab Video Ngủ:** Chuyên dùng để tạo video dài (3-4 tiếng) loop liền mạch. Giao diện chia thành 2 phần (Đầu vào File và Tùy chọn).
- **Tab Hàng Đợi:** Quản lý tiến trình render tự động (Hàng đợi) và xem lại kết quả (Lịch sử render).

## LUỒNG DỮ LIỆU VÀ GIAO DIỆN
- Bám sát `screen3_video_ngu.html` và `screen6_hang_doi.html`.
- **Video Ngủ:** Dùng `QGridLayout` cho các ô input đường dẫn, `QHBoxLayout` cho các cài đặt nhỏ (Visualizer, Fade tiếng).
- **Hàng Đợi:** Dùng `QListWidget` cho danh sách đang chờ, và `QTableWidget` cho danh sách lịch sử. Tích hợp thanh công cụ (Xóa, Xóa hết, Mở thư mục).
- Tương tự các Phase trước, tất cả các nút bấm liên quan đến backend (Tạo video, Render cả hàng đợi) đều trỏ về MessageBox Stub.

## CÁC FILE CẦN CAN THIỆP
- `ui/tabs/tab_sleep.py` (Tạo mới)
- `ui/tabs/tab_queue.py` (Tạo mới)
- `ui/main_window.py` (Cập nhật nạp cả 2 tab vào vị trí 3 và 4)
- `ui/style.qss` (Thêm style cho QListWidget, QTableWidget)
