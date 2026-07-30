# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 11)

## MỤC TIÊU CỦA PLANNER
Phase 11 là mảnh ghép cuối cùng của lộ trình tích hợp (Wiring). Mục tiêu là đánh thức **Hàng Đợi (Queue Manager)** để nó thực sự làm việc.
Tại Phase 8, `worker_queue.py` chỉ chạy lặp qua các Job bằng `time.sleep(1.5)`. Tại Phase 11, Worker này sẽ nhặt từng Data Dictionary của các Video đang chờ, sau đó truyền vào hàm `auto_edit.render_video(...)` đã bóc tách ở Phase 9 để kết xuất (render) nối tiếp nhau.

## NHIỆM VỤ CỐT LÕI
1. **Tích hợp Gọi thật:** Thay vì `time.sleep`, `worker_queue.py` sẽ nạp tham số của Job hiện tại và gọi `render_video`.
2. **Theo dõi đa tiến trình:** Cần truyền được `progress_cb` sâu vào trong `render_video` cho từng Job một cách riêng biệt để UI Console vẫn hiển thị đúng log của Video đang chạy mà không bị loạn.

## CÁC FILE CẦN CAN THIỆP
- `core/worker_queue.py` (Cập nhật: Bỏ `time.sleep`, gọi hàm render thật)
