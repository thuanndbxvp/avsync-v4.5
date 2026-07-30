# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 8

Tuân thủ nghiêm ngặt các bước dưới đây để nhân rộng pattern QThread cho toàn bộ các Tab xử lý video.

## BƯỚC 1: Xây dựng Worker cho Render Video
Tạo file `core/worker_render.py` với nội dung:
```python
# -*- coding: utf-8 -*-
from PySide6.QtCore import QThread, Signal

class RenderWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, data_dict):
        super().__init__()
        self.data = data_dict
        
    def run(self):
        self.log_signal.emit("[System] Bắt đầu tiến trình Render Video...", "#0066FF")
        try:
            import auto_edit as ae
            # Bóc tách thông tin từ data_dict
            cfg = self.data.get("cfg", {})
            srt = self.data.get("srt", "")
            img_dir = self.data.get("img_dir", "")
            output = self.data.get("output", "")
            
            self.log_signal.emit(f"• Chuẩn bị ghép video: {output}", "#D4D4D4")
            
            # Hàm callback truyền tiến độ
            def prog(msg):
                self.log_signal.emit(f"   {msg}", "#D4D4D4")
                
            # [POC Integration] Gọi API thật
            # ae.render_video(srt, img_dir, output, cfg, progress_cb=prog)
            self.log_signal.emit("✅ Đã gọi auto_edit.render_video(...) thành công (POC)!", "#28A745")
            
            self.finished_signal.emit(True, "Render Video hoàn tất!")
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi render: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```
*Tầng 2: Mở `ui/tabs/tab_render.py`, import `RenderWorker` và sửa hàm `stub_action` ở nút RENDER VIDEO để gọi worker này, truyền data_dict tương tự Phase 7.*

## BƯỚC 2: Xây dựng Worker cho Video Ngủ
Tạo file `core/worker_sleep.py` với nội dung:
```python
# -*- coding: utf-8 -*-
from PySide6.QtCore import QThread, Signal

class SleepWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, data_dict):
        super().__init__()
        self.data = data_dict
        
    def run(self):
        self.log_signal.emit("[System] Bắt đầu tạo Video Ngủ dài...", "#0066FF")
        try:
            import auto_edit as ae
            # Bóc tách thông tin
            bg_path = self.data.get("bg", "")
            audio_path = self.data.get("audio", "")
            out_path = self.data.get("output", "")
            
            self.log_signal.emit(f"• Xử lý Video Ngủ: {out_path}", "#D4D4D4")
            
            def prog(msg):
                self.log_signal.emit(f"   {msg}", "#D4D4D4")
                
            # [POC Integration] Gọi API thật
            # ae.render_sleep_video(bg_path, audio_path, out_path, progress_cb=prog)
            self.log_signal.emit("✅ Đã gọi auto_edit.render_sleep_video(...) thành công (POC)!", "#28A745")
            
            self.finished_signal.emit(True, "Tạo Video Ngủ hoàn tất!")
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi Video Ngủ: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```
*Tầng 2: Mở `ui/tabs/tab_sleep.py`, import `SleepWorker` và sửa nút bấm gọi worker.*

## BƯỚC 3: Xây dựng Worker cho Hàng Đợi (Queue Manager)
Tạo file `core/worker_queue.py` với nội dung:
```python
# -*- coding: utf-8 -*-
import time
from PySide6.QtCore import QThread, Signal

class QueueWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)
    progress_signal = Signal(int) # index của item đang chạy
    
    def __init__(self, queue_jobs):
        super().__init__()
        self.jobs = queue_jobs # list các data_dict
        
    def run(self):
        self.log_signal.emit(f"[System] Bắt đầu render Hàng đợi ({len(self.jobs)} jobs)...", "#0066FF")
        try:
            import auto_edit as ae
            
            for idx, job in enumerate(self.jobs):
                self.log_signal.emit(f"▶ Đang xử lý Job {idx+1}/{len(self.jobs)}: {job.get('output', 'N/A')}", "#E3F2FD")
                self.progress_signal.emit(idx)
                
                # Gọi API thật tùy theo loại job
                # ae.render_video(...)
                
                # Giả lập thời gian chạy cho POC
                time.sleep(1.5)
                
                self.log_signal.emit(f"✅ Xong Job {idx+1}!", "#28A745")
                
            self.finished_signal.emit(True, "Đã chạy xong toàn bộ hàng đợi!")
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi Hàng đợi: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```
*Tầng 2: Mở `ui/tabs/tab_queue.py`, import `QueueWorker`. Lấy toàn bộ items trong `QListWidget`, tạo list dict và ném vào worker. Bắt `progress_signal` để tô đậm item đang chạy trên UI.*

## BƯỚC 4: Kiểm định (Audit)
Tầng 2 chạy lệnh `python app.py`. 
Click lần lượt vào 3 Tab: Render, Video Ngủ, Hàng Đợi và bấm các nút xử lý chính.
Quan sát Console Log:
- Đảm bảo các tiến trình được chạy ngầm dưới nền.
- Đảm bảo UI không bị "Not Responding" (treo cứng) trong lúc có dòng log hiện ra.
Nếu các tab hoạt động tương tự như Tab Tạo Prompt, Phase 8 thành công mĩ mãn!
