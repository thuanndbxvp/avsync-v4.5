# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 11

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối (Wire) thật trình quản lý Hàng đợi (Queue).

## BƯỚC 1: Cập nhật `core/worker_queue.py`
Mở file `core/worker_queue.py` (đã tạo ở Phase 8) và thay đoạn POC (time.sleep) bằng lời gọi hàm thật:
```python
        try:
            # Import hàm render đã bóc tách từ Phase 9
            import auto_edit as ae
            
            for idx, job in enumerate(self.jobs):
                # job là 1 dictionary chứa data của từng video trong hàng đợi
                output_name = job.get("output", f"Video_{idx+1}")
                self.log_signal.emit(f"▶ Đang xử lý Job {idx+1}/{len(self.jobs)}: {output_name}", "#E3F2FD")
                
                # Emit signal báo cho giao diện (tô màu ListWidget)
                self.progress_signal.emit(idx)
                
                # Callback đặc biệt cho Job này
                def prog(msg):
                    self.log_signal.emit(f"   [Job {idx+1}] {msg}", "#D4D4D4")
                
                # Trích xuất dữ liệu Job
                cfg = job.get("cfg", {})
                srt = job.get("srt", "")
                img_dir = job.get("img_dir", "")
                
                # GỌI HÀM THẬT (Chạy tuần tự, blocking trong thread này)
                if hasattr(ae, "render_video"):
                    ae.render_video(srt, img_dir, output_name, cfg, progress_cb=prog)
                else:
                    self.log_signal.emit(f"[Error] Thiếu hàm render_video trong auto_edit.py", "#ba1a1a")
                    raise AttributeError("Thiếu hàm lõi render_video")
                
                self.log_signal.emit(f"✅ Xong Job {idx+1}: {output_name}!", "#28A745")
                
            self.finished_signal.emit(True, f"Đã chạy xong toàn bộ {len(self.jobs)} job(s)!")
            
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi Hàng đợi tại Job {idx+1}: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```

## BƯỚC 2: Kiểm định (Audit) Phase 11 & Toàn dự án
Chạy lệnh `python app.py`. 
1. Cấu hình 2 video khác nhau ở Tab Render Video, ấn "Thêm vào hàng đợi".
2. Sang Tab Hàng đợi, ấn **RENDER CẢ HÀNG ĐỢI**.
3. Xem Console Log: Nó phải in được tiến trình của Job 1, chạy xong Job 1 nhảy sang Job 2 và in tiếp.
4. Thư mục đầu ra có đủ 2 file MP4 thì **XIN CHÚC MỪNG**, toàn bộ quá trình tái cấu trúc PySide6 đồ sộ này đã THÀNH CÔNG RỰC RỠ 100%!
