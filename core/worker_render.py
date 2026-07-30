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

            # GỌI HÀM THẬT VỪA TẠO Ở BƯỚC 1
            ae.render_video(srt, img_dir, output, cfg, progress_cb=prog)

            self.log_signal.emit("✅ Đã hoàn tất Render Video!", "#28A745")

            self.finished_signal.emit(True, "Render Video hoàn tất!")
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi render: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))