# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 10

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối (Wire) thật tính năng làm Video Ngủ.

## BƯỚC 1: Khảo sát & Bóc tách logic Video Ngủ
1. Mở file `app_legacy.py`, tìm đoạn code liên quan đến chức năng làm Video Ngủ (từ khóa: `run_make_sleep`, `_build_sleep_thread` hoặc các lệnh gọi ffmpeg tạo loop ảnh và audio).
2. Tạo mới file `core/sleep_video.py`.
3. Bê toàn bộ khối code xử lý logic Video Ngủ vào trong một function gọn gàng:
```python
def render_sleep_video(bg_path, audio_path, out_path, config=None, progress_cb=None):
    """
    Hàm lõi tạo Video Ngủ (dài 3-4 tiếng).
    """
    def log(msg):
        if progress_cb: progress_cb(msg)
        else: print(msg)
        
    log(f"Bắt đầu làm Video Ngủ: BG={bg_path}, AUDIO={audio_path}...")
    
    # [TẦNG 2 BÊ LOGIC FFMPEG TỪ APP_LEGACY.PY VÀO ĐÂY]
    # ...
    
    log("Tạo Video Ngủ hoàn tất!")
    return True
```

## BƯỚC 2: Cập nhật `core/worker_sleep.py`
Mở file `core/worker_sleep.py` và thay thế đoạn comment POC bằng lời gọi hàm thật:
```python
        try:
            # Import module vừa tạo
            from core.sleep_video import render_sleep_video
            
            # Bóc tách thông tin
            bg_path = self.data.get("bg", "")
            audio_path = self.data.get("audio", "")
            out_path = self.data.get("output", "")
            cfg = self.data.get("cfg", {})
            
            self.log_signal.emit(f"• Xử lý Video Ngủ: {out_path}", "#D4D4D4")
            
            def prog(msg):
                self.log_signal.emit(f"   {msg}", "#D4D4D4")
                
            # GỌI HÀM THẬT
            render_sleep_video(bg_path, audio_path, out_path, config=cfg, progress_cb=prog)
            
            self.log_signal.emit("✅ Đã hoàn thành Video Ngủ!", "#28A745")
            self.finished_signal.emit(True, "Tạo Video Ngủ hoàn tất!")
            
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi Video Ngủ: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```

## BƯỚC 3: Kiểm định (Audit)
Chạy lệnh `python app.py`. 
Vào Tab **Video Ngủ**, chọn ảnh/video nền, chọn đoạn âm thanh dài (nhạc lofi/mưa), chọn đầu ra và bấm **TẠO VIDEO NGỦ**.
Nếu UI không đơ, Console nảy log quá trình, và có file output xem được trơn tru -> Phase 10 thành công!
