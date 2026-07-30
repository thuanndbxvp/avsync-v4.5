# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QRadioButton, QButtonGroup, QFileDialog,
    QMessageBox, QScrollArea, QCheckBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from core.worker_render import RenderWorker

class RenderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # 1. Tạo Scroll Area bọc toàn bộ Tab
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll.setWidget(self.scroll_content)

        # Bố cục chính
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)

        # Bố cục bên trong scroll content
        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ------------------- CARD 1: NGUYÊN LIỆU & HỒ SƠ -------------------
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)
        layout1.setContentsMargins(20, 20, 20, 20)

        # Hồ sơ kênh
        row_channel = QHBoxLayout()
        lbl_channel = QLabel("📺 Hồ sơ kênh:")
        lbl_channel.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")
        self.cmb_channel = QComboBox()
        self.cmb_channel.setFixedWidth(200)
        btn_save_channel = QPushButton("💾 Lưu kênh...")
        btn_del_channel = QPushButton("🗑")
        row_channel.addWidget(lbl_channel)
        row_channel.addWidget(self.cmb_channel)
        row_channel.addWidget(btn_save_channel)
        row_channel.addWidget(btn_del_channel)
        row_channel.addStretch()
        layout1.addLayout(row_channel)

        # Lưới Nguyên liệu
        grid1 = QGridLayout()
        grid1.setColumnStretch(1, 1)
        grid1.setVerticalSpacing(12)
        grid1.setContentsMargins(0, 16, 0, 0)

        # Định nghĩa các hàng input
        inputs = [
            ("File PHỤ ĐỀ (SRT):", "subtitle.srt"),
            ("Thư mục ẢNH/CLIP:", "images"),
            ("File VOICEOVER:", ""),
            ("📋 File bảng cảnh:", ""),
            ("Xuất ra MP4:", "final.mp4")
        ]

        self.path_inputs = {}
        for row, (label_text, default_val) in enumerate(inputs):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("border: none; font-weight: 500;")
            inp = QLineEdit(default_val)
            btn = QPushButton("Chọn...")
            btn.setStyleSheet("background: #F8F9FA; border: 1px solid #DEE2E6; padding: 4px 10px; border-radius: 4px;")
            btn.clicked.connect(lambda checked, idx=row: self.stub_action(f"Chọn đường dẫn cho {label_text}"))

            box = QHBoxLayout()
            box.addWidget(inp)
            box.addWidget(btn)

            grid1.addWidget(lbl, row, 0)
            grid1.addLayout(box, row, 1)
            self.path_inputs[label_text] = inp

        layout1.addLayout(grid1)
        layout.addWidget(card1)

        # ------------------- CARD 2: TÙY CHỌN GHÉP VIDEO -------------------
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)
        layout2.setContentsMargins(20, 20, 20, 20)
        layout2.setSpacing(16)

        lbl_title2 = QLabel("⚙️ Tùy chọn ghép")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        # Khung hình
        row_aspect = QHBoxLayout()
        lbl_aspect = QLabel("Khung hình:")
        lbl_aspect.setStyleSheet("border: none; font-weight: bold;")
        self.rad_16_9 = QRadioButton("16:9 ngang (YouTube)")
        self.rad_9_16 = QRadioButton("9:16 dọc (Shorts/TikTok)")
        self.rad_16_9.setChecked(True)
        row_aspect.addWidget(lbl_aspect)
        row_aspect.addWidget(self.rad_16_9)
        row_aspect.addWidget(self.rad_9_16)
        row_aspect.addStretch()
        layout2.addLayout(row_aspect)

        # Hiệu ứng
        row_fx = QHBoxLayout()
        self.chk_kenburns = QCheckBox("Ken Burns (zoom ảnh tĩnh)")
        self.chk_sub = QCheckBox("Chèn phụ đề")
        self.chk_sub.setChecked(True)
        self.chk_crossfade = QCheckBox("Crossfade ảnh")
        row_fx.addWidget(self.chk_kenburns)
        row_fx.addWidget(self.chk_sub)
        row_fx.addWidget(self.chk_crossfade)
        row_fx.addStretch()
        layout2.addLayout(row_fx)

        # Cài đặt Phụ đề
        lbl_sub_settings = QLabel("🖍 Cài đặt Phụ đề chuyên sâu:")
        lbl_sub_settings.setStyleSheet("font-weight: bold; margin-top: 10px; border: none;")
        layout2.addWidget(lbl_sub_settings)

        row_font = QHBoxLayout()
        row_font.addWidget(QLabel("Phông chữ:"))
        self.cmb_font = QComboBox()
        self.cmb_font.addItems(["Arial Black", "Arial", "Impact", "Segoe UI Black"])
        row_font.addWidget(self.cmb_font)

        row_font.addWidget(QLabel(" Cỡ chữ:"))
        self.spin_fontsize = QSpinBox()
        self.spin_fontsize.setRange(20, 140)
        self.spin_fontsize.setValue(52)
        row_font.addWidget(self.spin_fontsize)
        row_font.addStretch()
        layout2.addLayout(row_font)

        layout.addWidget(card2)

        # ------------------- 3. ACTION AREA -------------------
        action_layout = QHBoxLayout()

        self.btn_render = QPushButton("▶ RENDER VIDEO")
        self.btn_render.setStyleSheet("""
            QPushButton {
                background-color: #0066FF; color: white;
                padding: 12px 24px; font-weight: bold; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #0052CC; }
        """)

        self.btn_preview = QPushButton("👁 Xem trước")
        self.btn_queue = QPushButton("➕ Thêm Hàng đợi")

        for btn in [self.btn_preview, self.btn_queue]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E3F2FD; color: #0066FF;
                    padding: 10px 16px; font-weight: bold; border-radius: 6px; border: none;
                }
                QPushButton:hover { background-color: #BBDEFB; }
            """)

        action_layout.addWidget(self.btn_render)
        action_layout.addWidget(self.btn_preview)
        action_layout.addWidget(self.btn_queue)
        action_layout.addStretch()

        # Kết nối Signals
        self.btn_render.clicked.connect(self.run_render)
        self.btn_preview.clicked.connect(lambda: self.stub_action("Chạy xem trước (Preview)..."))
        self.btn_queue.clicked.connect(lambda: self.stub_action("Thêm vào Hàng đợi..."))

        layout.addLayout(action_layout)
        layout.addStretch()

    def stub_action(self, msg):
        QMessageBox.information(self, "Đang xây dựng", f"{msg}\n(Tích hợp Backend ở Phase 4)")

    def run_render(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang chuẩn bị dữ liệu để Render...", "#D4D4D4")

        # Thu thập data dict (UI Phase 3 - stub)
        data = {
            "cfg": {},
            "srt": self.path_inputs["File PHỤ ĐỀ (SRT):"].text(),
            "img_dir": self.path_inputs["Thư mục ẢNH/CLIP:"].text(),
            "output": self.path_inputs["Xuất ra MP4:"].text(),
            "channel": self.cmb_channel.currentText(),
            "aspect": "16:9" if self.rad_16_9.isChecked() else "9:16",
            "kenburns": self.chk_kenburns.isChecked(),
            "sub": self.chk_sub.isChecked(),
            "crossfade": self.chk_crossfade.isChecked(),
            "font": self.cmb_font.currentText(),
            "fontsize": self.spin_fontsize.value()
        }

        # Khóa nút bấm
        self.btn_render.setEnabled(False)
        self.btn_render.setText("⏳ ĐANG RENDER...")

        # Chạy Worker
        self.worker = RenderWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.finished_signal.connect(self.on_render_finished)
        self.worker.start()

    def on_render_finished(self, success, msg):
        self.btn_render.setEnabled(True)
        self.btn_render.setText("▶ RENDER VIDEO")
        if success:
            QMessageBox.information(self, "Thành công", "Render Video hoàn tất!")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra:\n{msg}")
