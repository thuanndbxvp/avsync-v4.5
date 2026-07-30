# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget, QTextEdit
)
from PySide6.QtCore import Qt
from ui.tabs.tab_prompt import PromptTab
from ui.tabs.tab_render import RenderTab
from ui.tabs.tab_sleep import SleepTab
from ui.tabs.tab_queue import QueueTab
from ui.tabs.tab_settings import SettingsTab

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

        # Tab 1: Tạo Prompt
        self.tab_prompt = PromptTab()
        self.stacked_widget.addWidget(self.tab_prompt)

        # Tab 2: Render Video
        self.tab_render = RenderTab()
        self.stacked_widget.addWidget(self.tab_render)

        # Tab 3: Video Ngủ
        self.tab_sleep = SleepTab()
        self.stacked_widget.addWidget(self.tab_sleep)

        # Tab 4: Hàng Đợi
        self.tab_queue = QueueTab()
        self.stacked_widget.addWidget(self.tab_queue)

        # Tab 5: Cài đặt
        self.tab_settings = SettingsTab()
        self.stacked_widget.addWidget(self.tab_settings)

        # Lúc này stacked_widget đã có đủ 5 tab thật!

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

    def append_log(self, text, color="#D4D4D4"):
        html = f'<span style="color: {color};">{text}</span>'
        self.console_log.append(html)

    # ---------------------------------------------------------------- M6 — Queue bridge
    def add_queue_job(self, job_dict):
        """API public: Tab Render push job vào Tab Queue.
        Forward tới QueueTab.add_job() — nếu Queue tab chưa build thì warning.
        """
        if hasattr(self, "tab_queue") and hasattr(self.tab_queue, "add_job"):
            self.tab_queue.add_job(job_dict)
            self.append_log(
                f"➕ Đã thêm job vào hàng đợi: {job_dict.get('output', '?')}",
                "#28A745",
            )
            # Auto-switch sang Queue tab để user thấy
            self.switch_tab(3)
        else:
            self.append_log(
                f"[WARN] QueueTab chưa khởi tạo hoặc không có add_job()",
                "#ba1a1a",
            )

    def switch_tab(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)
