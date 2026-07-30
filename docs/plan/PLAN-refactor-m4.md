# KIẾN TRÚC TỔNG QUAN: CORE REFACTORING (MILESTONE 4)

## MỤC TIÊU CỦA PLANNER
Milestone 4 (M4) là bước chốt chặn để dọn dẹp và đóng gói. Tại bước này, hệ thống UI PySide6 sẽ nói chuyện mượt mà với lớp Service bất đồng bộ mới thông qua các QThread. Các file code cũ chứa đầy nợ kỹ thuật sẽ chính thức bị gắn cờ "Lỗi thời" (Deprecated) và trở thành các Shim (vỏ bọc) rỗng.

## NHIỆM VỤ CỐT LÕI
1. **Worker Integration (`core/worker_*.py`)**:
   - Cập nhật các QThread để sử dụng vòng lặp bất đồng bộ (`asyncio.run()`), cho phép truyền Signal "Hủy" từ UI để ngắt quá trình render/AI giữa chừng.
2. **Dọn dẹp God Objects**:
   - Biến `auto_edit.py`, `ai_prompts.py` và `sleep_video.py` thành các file chỉ chứa vài dòng `import` và `warnings.warn("Deprecated")`. Đảm bảo code rác bị xóa sạch để nâng Code Coverage.
3. **Caching & Observability (Tùy chọn nâng cao)**:
   - Thêm bộ đệm LRU cho các hàm cấu hình nặng. Thêm Log có cấu trúc (JSON) để dễ debug.

## CÁC FILE CẦN CAN THIỆP
- `core/worker_*.py`
- `auto_edit.py`, `ai_prompts.py`, `sleep_video.py`
