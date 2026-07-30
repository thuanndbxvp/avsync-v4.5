# MICRO-STEP EXECUTION WORKFLOW: REFACTOR MILESTONE 4

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối Worker và Dọn rác (Cleanup).

## BƯỚC 1: Nâng cấp QThread chạy Async
1. Mở `core/worker_render.py` (và các worker khác).
2. Thêm một cờ `self.is_cancelled = False` để lắng nghe thao tác hủy từ UI.
3. Trong hàm `run()`, thay thế lời gọi đồng bộ bằng:
```python
import asyncio
from services.render_service import render_video_async

def run(self):
    try:
        # Chạy vòng lặp sự kiện
        asyncio.run(render_video_async(..., cancel_token=self.is_cancelled))
    except asyncio.CancelledError:
        self.log_signal.emit("Đã hủy bởi người dùng!", "red")
```

## BƯỚC 2: Rút gọn God Objects thành Shim
1. Mở `auto_edit.py`. Xóa sạch toàn bộ code không liên quan đến argparse (CLI parsing).
2. Thêm cảnh báo ở đầu file:
```python
import warnings
warnings.warn("auto_edit.py is deprecated. Use services/render_service.py instead.", DeprecationWarning)
```
3. Làm tương tự với `ai_prompts.py` và `sleep_video.py`.

## BƯỚC 3: Tổng kiểm tra (Final Audit)
- Mở PySide6 App, chạy thử toàn bộ 5 Tab từ trên xuống dưới.
- Đảm bảo app không bị đứng khung hình, thanh tiến trình chạy mượt, và khi bấm nút Dừng/Hủy thì tiến trình dừng ngay lập tức.
- XONG! Chúc mừng bạn đã Refactor thành công dự án cực khủng này!
