# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 1

Tuân thủ nghiêm ngặt các bước dưới đây. Tầng 2 (Coder) chỉ cần copy-paste và kiểm định lại linter.

## BƯỚC 1: Cập nhật thư viện
Thêm `PySide6` vào cuối file `requirements.txt`.
(Cài đặt vào môi trường `venv` nếu cần thiết).

## BƯỚC 2: Đổi tên file cũ
Dùng lệnh để đổi tên `app.py` thành `app_legacy.py`. (Giữ nguyên toàn bộ code cũ bên trong).

> ⚠️ **LƯU Ý**: `run.bat` hiện đang hard-code gọi `app.py` cũ. Theo quyết định kiến trúc đã chốt (xem `AUDIT-REPORT-pyside6-phase1.md`, Q1=Q1B), Tầng 2 **KHÔNG đụng `run.bat`** ở Phase 1. User muốn chạy GUI PySide6 mới sẽ gõ `python app.py` trực tiếp; `run.bat` vẫn mở GUI Tkinter cũ (`app_legacy.py` qua symlink/đường tắt Phase 2 sẽ được xử lý sau).

## BƯỚC 2.5: Cập nhật `preflight.py` (chốt ở Q2=Q2A)
Sau khi `app.py` → `app_legacy.py`, `preflight.py` đang có `import app` sẽ nổ `ModuleNotFoundError`. Tầng 2 tách thành 2 sub-check rõ ràng:

1. **Sub-check A — `app_legacy.py`** (giữ nguyên): compile, AST trùng tên, đọc `default_config` qua `import app_legacy as app_legacy_module`. Lấy biến thành `defaults = set(app_legacy_module.default_config().keys())`.
2. **Sub-check B — `app.py` mới** (PySide6 stub Phase 1): chỉ cần `py_compile` pass + `import app; assert isinstance(app.QApplication_proxy, type)` hoặc đơn giản hơn: thử `import app` không nổ là đủ (vì stub PySide6 chỉ có `main()`).

Cập nhật dòng `FILES = [...]` ở `preflight.py:30-31` thành `["app_legacy.py", "app.py", "auto_edit.py", ...]`.
Cập nhật dòng `import app # noqa` ở `preflight.py:79` thành `import app_legacy as app_legacy_module` (và đổi `app.default_config` → `app_legacy_module.default_config`).
Cập nhật dòng `a = app.App(r)` ở `preflight.py:101` thành `a = app_legacy_module.App(r)`.
Cập nhật dòng `src = open("app.py", ...)` ở `preflight.py:78` thành `src = open("app_legacy.py", ...)`.

> Lưu ý: GUI smoke test (Phase 4 của preflight) vẫn chạy trên `app_legacy.App` để đảm bảo logic cũ không vỡ trong Phase 1; sang Phase 2 sẽ có bước smoke riêng cho PySide6.

## BƯỚC 2.6: Cập nhật `build_release.bat` (chốt ở Q3=Q3A)
Đổi target Nuitka từ `app.py` (Tkinter) sang `app.py` (PySide6) và plugin từ `tk-inter` sang `pyside6`:

- Dòng 29 hiện: `python -m nuitka --standalone --onefile --enable-plugin=tk-inter --include-package=cryptography --include-package=certifi ... --output-filename=AutoEditVideo.exe app.py`
- Đổi thành: bỏ `--enable-plugin=tk-inter`, thêm `--enable-plugin=pyside6 --include-package=PySide6`. Comment cũ gần plugin giải thích "true positive: Nuitka onefile bị Defender đánh dấu nhầm Trojan" vẫn giữ.

## BƯỚC 3: Tạo cấu trúc thư mục UI
Tạo các thư mục `ui` và `ui/tabs`, kèm theo file `__init__.py` rỗng bên trong chúng để biến thành Python packages.

## BƯỚC 4: Tạo file CSS (QSS)
Tạo file `ui/style.qss` với nội dung sau:
```css
/* style.qss - Dựa trên Design System Streamline Logic */

QMainWindow, QDialog {
    background-color: #F8F9FA;
}

#Sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #DEE2E6;
}

#Sidebar QPushButton {
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    background-color: transparent;
    color: #424656;
    font-family: "Inter", sans-serif;
    font-size: 14px;
    font-weight: 500;
}

#Sidebar QPushButton:hover {
    background-color: #F2F3FF;
}

#Sidebar QPushButton:checked {
    background-color: #E6E7F4;
    color: #0066FF;
    font-weight: bold;
    border-left: 4px solid #0066FF;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
}

#TopBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #DEE2E6;
}

#ConsoleFrame {
    background-color: #1E1E1E;
    border-top: 1px solid #424656;
}

#ConsoleLog {
    background-color: #1E1E1E;
    color: #D4D4D4;
    font-family: "Fira Sans", monospace;
    font-size: 13px;
    border: none;
}
```

## BƯỚC 5: Xây dựng Khung MainWindow
Tạo file `ui/main_window.py`:
```python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QStackedWidget, QTextEdit
)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PeiPei Auto Edit Video 🎬 (PySide6)")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        
        # Bố cục chính
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setup_sidebar()
        self.setup_right_panel()

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(260)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(16, 24, 16, 24)
        
        # Logo & App Name
        self.lbl_logo = QLabel("PeiPei Auto Edit")
        self.lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #0066FF;")
        self.sidebar_layout.addWidget(self.lbl_logo)
        
        self.lbl_version = QLabel("v1.2.7")
        self.lbl_version.setStyleSheet("color: #727687; font-size: 12px; margin-bottom: 16px;")
        self.sidebar_layout.addWidget(self.lbl_version)
        
        # Menu Buttons
        self.nav_buttons = []
        menus = [
            "✍️ Tạo Prompt", "🎬 Render Video", "🌙 Video ngủ", 
            "📋 Hàng đợi", "⚙️ Cài đặt"
        ]
        
        for i, text in enumerate(menus):
            btn = QPushButton(text)
            btn.setCheckable(True)
            if i == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            self.nav_buttons.append(btn)
            self.sidebar_layout.addWidget(btn)
            
        self.sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)

    def setup_right_panel(self):
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        # Top Bar
        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setFixedHeight(64)
        self.top_layout = QHBoxLayout(self.top_bar)
        self.top_layout.setContentsMargins(24, 0, 24, 0)
        
        self.lbl_title = QLabel("Trạng thái: Sẵn sàng")
        self.top_layout.addWidget(self.lbl_title)
        self.top_layout.addStretch()
        self.right_layout.addWidget(self.top_bar)
        
        # Main Canvas (Tabs)
        self.stacked_widget = QStackedWidget()
        self.right_layout.addWidget(self.stacked_widget, 1)
        
        # Tạo 5 tab rỗng giữ chỗ
        for i in range(5):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel(f"Đang chờ thi công Tab {i+1}... (Phase tiếp theo)"))
            self.stacked_widget.addWidget(page)
            
        # Bottom Console
        self.console_frame = QFrame()
        self.console_frame.setObjectName("ConsoleFrame")
        self.console_frame.setFixedHeight(200)
        self.console_layout = QVBoxLayout(self.console_frame)
        self.console_layout.setContentsMargins(16, 8, 16, 16)
        
        self.lbl_console = QLabel("Nhật ký hệ thống (Console Logs)")
        self.lbl_console.setStyleSheet("color: #727687; font-size: 11px; font-weight: bold;")
        self.console_layout.addWidget(self.lbl_console)
        
        self.console_log = QTextEdit()
        self.console_log.setObjectName("ConsoleLog")
        self.console_log.setReadOnly(True)
        self.console_log.append("[System] Đã khởi tạo kiến trúc PySide6 thành công.")
        self.console_layout.addWidget(self.console_log)
        
        self.right_layout.addWidget(self.console_frame)
        self.main_layout.addWidget(self.right_panel)

    def switch_tab(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)
```

## BƯỚC 6: Tạo app.py mới (Entry point)
Tạo file `app.py` mới toanh:
```python
# -*- coding: utf-8 -*-
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
```

## BƯỚC 7: Kiểm định (Audit)
Tầng 2 sau khi copy/paste các bước trên, hãy chạy lệnh:
`python app.py`
Nếu giao diện khởi tạo thành công với cấu trúc chuẩn (Sidebar, Header, Console, các Tabs rỗng), hãy xuất AUDIT-REPORT báo cáo tiến độ và đóng task Phase 1.
