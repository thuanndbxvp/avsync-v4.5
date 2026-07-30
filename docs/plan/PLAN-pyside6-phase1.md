# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 1)

Dự án hiện đang sử dụng `tkinter` với toàn bộ code giao diện (2600+ dòng) bị nhồi nhét vào một file duy nhất `app.py`. Code xử lý logic (chạy ngầm, đọc config) bị trộn lẫn với mã giao diện. 
Điều này gây ra Code Smell nghiêm trọng (God Object) và làm quá trình tích hợp bản thiết kế mới (Tailwind CSS/Stitch) trở nên bất khả thi.

## Quyết Định Của Planner
Để an toàn và dễ dàng cho Tầng 2, chúng ta sẽ chia quá trình đập đi xây lại thành nhiều Phase.
Phase 1 tập trung vào:
1. Đổi tên `app.py` cũ thành `app_legacy.py` để cất giữ logic, không xóa ngay.
2. Xây dựng lại `app.py` mới tinh, khởi tạo ứng dụng PySide6.
3. Tạo kiến trúc thư mục mới `ui/` và `ui/tabs/`.
4. Viết file `ui/main_window.py` để tạo khung sườn (Sidebar trái, Header trên, Console log dưới đáy) theo chuẩn HTML từ bản thiết kế.
5. Setup file `ui/style.qss` để định nghĩa màu sắc chủ đạo.

## Luồng dữ liệu (Data flow)
`app.py` (QApplication) -> gọi `MainWindow` -> nạp `style.qss` -> load 5 Tab rỗng (giữ chỗ) vào `QStackedWidget`.

## Các file cần can thiệp trong Phase 1
- `requirements.txt` (thêm PySide6)
- `app.py` -> đổi tên thành `app_legacy.py`
- `app.py` (mới)
- `ui/__init__.py`
- `ui/style.qss`
- `ui/main_window.py`
- `ui/tabs/__init__.py`
