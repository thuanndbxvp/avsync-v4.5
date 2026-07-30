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
            from sleep_video import render_sleep_video
            # Bóc tách thông tin
            bg_path = self.data.get("bg", "")
            audio_path = self.data.get("audio", "")
            out_path = self.data.get("output", "")
            cfg = self.data.get("cfg", {})

            self.log_signal.emit(f"• Xử lý Video Ngủ: {out_path}", "#D4D4D4")

            def prog(msg):
                self.log_signal.emit(f"   {msg}", "#D4D4D4")

            # GỌI HÀM THẬT — sleep_video.render_sleep_video(...)
            render_sleep_video(bg_path, audio_path, out_path, config=cfg, progress_cb=prog)

            self.log_signal.emit("✅ Đã hoàn thành Video Ngủ!", "#28A745")
            self.finished_signal.emit(True, "Tạo Video Ngủ hoàn tất!")
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi Video Ngủ: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))