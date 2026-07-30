# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 9)

## MỤC TIÊU CỦA PLANNER
Tiếp nối sự thành công của cơ chế Worker chạy ngầm (QThread), Phase 9 sẽ tiến hành **Wire (đấu nối) thật sự** chức năng Render Video.

Hiện tại, file `auto_edit.py` là một script độc lập, logic chạy chính nằm trong khối `if __name__ == '__main__':` (hoặc hàm `main()`) cùng với `argparse`. Để PySide6 có thể gọi mượt mà mà không phải dùng `subprocess`, chúng ta cần bóc tách khối logic này thành một top-level function.

## NHIỆM VỤ CỐT LÕI (REFACTORING)
1. **Trong `auto_edit.py`**: Refactor (tái cấu trúc) khối xử lý chính thành hàm `render_video(srt, img_dir, output, cfg, progress_cb)`. Khối CLI (`argparse`) cũ sẽ chỉ việc parse tham số và gọi lại hàm `render_video` này. Đảm bảo cấu trúc cũ (chạy qua Command Line) không bị hỏng (Zero regression risk).
2. **Trong `worker_render.py`**: Loại bỏ code POC giả lập, thay vào đó gọi hàm `auto_edit.render_video` thật. Truyền callback tiến trình (`progress_cb`) để bắn text log lên UI.

## CÁC FILE CẦN CAN THIỆP
- `auto_edit.py` (Refactor: Tạo hàm `render_video`)
- `core/worker_render.py` (Cập nhật: Bỏ POC, Wire logic thật)
