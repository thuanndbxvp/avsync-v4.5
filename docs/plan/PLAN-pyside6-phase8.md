# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 8)

## MỤC TIÊU CỦA PLANNER
Sau khi Phase 7 chứng minh thành công cơ chế `QThread` không làm nghẽn giao diện (UI non-blocking) khi gọi các hàm xử lý tốn thời gian, **Phase 8** sẽ tiến hành nhân rộng (Scale up) pattern này cho 3 Tab còn lại.

## PHẠM VI NHÂN RỘNG
1. **Tab Render Video:** 
   - Đấu nối `ui/tabs/tab_render.py` vào `core/worker_render.py`.
   - Worker này chịu trách nhiệm gọi hàm lõi `auto_edit.render_video(...)`.
2. **Tab Video Ngủ:**
   - Đấu nối `ui/tabs/tab_sleep.py` vào `core/worker_sleep.py`.
   - Worker này gọi hàm lõi `sleep_video.py` hoặc `auto_edit.render_sleep_video(...)`.
3. **Tab Hàng Đợi:**
   - Đấu nối `ui/tabs/tab_queue.py` vào `core/worker_queue.py`.
   - Worker đặc biệt này sẽ quản lý một danh sách các jobs (đa luồng nối tiếp), lần lượt lấy job từ hàng đợi ra xử lý và trả log/tiến trình về giao diện.

## LUỒNG DỮ LIỆU
Các Tab UI sẽ chỉ làm nhiệm vụ thu thập Data Dictionary, vô hiệu hóa các nút bấm, sau đó quăng Data cho Worker. Worker xử lý xong sẽ emit signal `finished_signal` để UI kích hoạt lại các nút bấm. Trong suốt quá trình, `log_signal` liên tục nhả text về `ConsoleLog` của `MainWindow`.
