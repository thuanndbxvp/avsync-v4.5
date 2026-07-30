# -*- coding: utf-8 -*-
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
        idx = -1
        try:
            import auto_edit as ae

            if not hasattr(ae, "render_video"):
                self.log_signal.emit("[Error] Thiếu hàm render_video trong auto_edit.py", "#ba1a1a")
                raise AttributeError("Thiếu hàm lõi render_video (Phase 9 chưa wire?)")

            for idx, job in enumerate(self.jobs):
                output_name = job.get("output", f"Video_{idx+1}")
                self.log_signal.emit(f"▶ Đang xử lý Job {idx+1}/{len(self.jobs)}: {output_name}", "#E3F2FD")

                # Highlight item đang chạy trên QListWidget
                self.progress_signal.emit(idx)

                # Callback TIẾN ĐỘ riêng cho Job này — bind early với _i=idx để tránh
                # late-binding bug nếu closure được lưu qua vòng for kế tiếp.
                def prog(msg, _i=idx):
                    self.log_signal.emit(f"   [Job {_i+1}] {msg}", "#D4D4D4")

                # Trích xuất dữ liệu Job
                cfg = job.get("cfg", {})
                srt = job.get("srt", "")
                img_dir = job.get("img_dir", "")

                # GỌI HÀM THẬT (tuần tự, blocking trong thread này)
                ae.render_video(srt, img_dir, output_name, cfg, progress_cb=prog)

                self.log_signal.emit(f"✅ Xong Job {idx+1}: {output_name}!", "#28A745")

            self.finished_signal.emit(True, f"Đã chạy xong toàn bộ {len(self.jobs)} job(s)!")
        except Exception as e:
            job_ctx = f" tại Job {idx+1}" if idx >= 0 else ""
            self.log_signal.emit(f"[Exception] Lỗi Hàng đợi{job_ctx}: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))