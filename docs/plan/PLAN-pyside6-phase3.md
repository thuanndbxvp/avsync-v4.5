# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 3)

## MỤC TIÊU CỦA PLANNER
Hoàn thiện **Tab Render Video** (Trang quan trọng nhất và nhiều cấu hình nhất). 
Vì số lượng cài đặt rất lớn (từ chọn file nguyên liệu, chỉnh sửa font/màu phụ đề đến setup hiệu ứng phim), Tab này bắt buộc phải sử dụng `QScrollArea` để người dùng có thể cuộn trang mà không bị tràn màn hình.

## LUỒNG DỮ LIỆU VÀ GIAO DIỆN
- Bám sát file thiết kế `screen2_render_video.html`.
- Các khối UI sẽ được chia thành 3 Card chính:
  1. **Hồ sơ kênh & Nguyên liệu** (Combobox chọn profile lưu sẵn + Đường dẫn files).
  2. **Tùy chọn ghép video** (Khung hình, hiệu ứng Ken Burns, Cài đặt Phụ đề chuyên sâu).
  3. **Thanh Action (Nút bấm)**: Render, Hàng đợi, Xem trước, Kiểm tra khớp nghĩa.
- Tạm thời gắn toàn bộ nút bấm vào logic "Stub" (MessageBox) để pass Audit UI trước khi tích hợp lõi logic ở Phase cuối.

## CÁC FILE CẦN CAN THIỆP
- `ui/tabs/tab_render.py` (Tạo mới)
- `ui/main_window.py` (Cập nhật để thay thế Tab giữ chỗ số 2 bằng `RenderTab`)
- `ui/style.qss` (Thêm style cho QScrollArea và QCheckBox)
