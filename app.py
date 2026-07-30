# -*- coding: utf-8 -*-
"""
Auto Edit Video — entry point PySide6 mới (Phase 1+).
  - Ứng dụng khởi tạo QApplication, nạp style.qss, mở MainWindow.
  - Ở Phase 1: stub rỗng, không có logic nghiệp vụ (đã chuyển sang ui/main_window.py + các file sau Phase 2).
  - GHI CHÚ Phase 1: file này KHÔNG có `default_config` hay `App` class —
    preflight.py tách riêng 2 sub-check (xem MSEW-pyside6-phase1.md#BƯỚC 2.5).
  - Để chạy GUI Tkinter cũ (Phase 0, đã ổn định), dùng: `python app_legacy.py`
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # Nạp QSS
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
