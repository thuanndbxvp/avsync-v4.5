# KIẾN TRÚC TỔNG QUAN: CHUYỂN ĐỔI GIAO DIỆN SANG PYSIDE6 (PHASE 2)

## QUYẾT ĐỊNH CỦA PLANNER (Phản hồi AUDIT-REPORT)
Tầng 2 đã làm rất tốt khi Audit bản vẽ. Tôi ghi nhận và chốt phương án xử lý như sau:
1. **Xung đột logic (Vấn đề #1):** Chúng ta sẽ **TẠO MỚI** UI trong `PromptTab`, hoàn toàn KHÔNG xóa hay sửa đổi hàm `_build_prompt` trong `app_legacy.py`. Ứng dụng cũ phải được giữ nguyên vẹn để hoạt động song song cho đến khi PySide6 app hoàn thiện 100%.
2. **UI tĩnh (Vấn đề #2):** Sẽ bổ sung việc gán Signal (`.clicked.connect(...)`) cho tất cả các nút bấm. Đối với các nút chạy AI (Tạo Prompt), do phần lõi gọi API đang dính chặt với class `App` cũ, chúng ta sẽ tạm thời nối nó vào hàm Stub (cảnh báo MessageBox: "Sẽ tích hợp Backend ở Phase 4").
3. **Mất config (Vấn đề #3):** Hàm `load_config` sẽ được nâng cấp: Nếu không tìm thấy file `config.local.json`, nó sẽ tự động fallback về cấu hình mặc định (có sẵn profile "Người que") giống hệt cách `app_legacy.py` đang làm.

## Mục Tiêu Của Planner
Dựng Widget `PromptTab` viết bằng PySide6 bám sát thiết kế HTML Tailwind (gồm các khối Card nền trắng viền xám, các input, button xanh đậm).

## Các File Cần Can Thiệp Trong Phase 2
- `ui/tabs/tab_prompt.py` (Tạo mới hoàn toàn)
- `ui/main_window.py` (Cập nhật import để nạp `PromptTab` vào `QStackedWidget`)
- `ui/style.qss` (Thêm CSS cho các input)
