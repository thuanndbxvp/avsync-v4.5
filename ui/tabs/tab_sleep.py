# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QMessageBox, QDoubleSpinBox
)
from core.worker_sleep import SleepWorker

class SleepTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ------------------- CARD 1: ĐẦU VÀO FILE -------------------
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)

        lbl_title1 = QLabel("📁 Khu vực Đầu vào File (Video ngủ dài 3-4 tiếng)")
        lbl_title1.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout1.addWidget(lbl_title1)

        grid1 = QGridLayout()
        grid1.setColumnStretch(1, 1)

        inputs = [
            ("NỀN (clip / ảnh):", "backgrounds"),
            ("AUDIO dài (kịch bản):", "scripts"),
            ("Âm thanh NỀN (tùy chọn):", ""),
            ("Xuất ra MP4:", "sleep.mp4")
        ]

        self.path_inputs = {}
        for row, (label_text, default_val) in enumerate(inputs):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("border: none; font-weight: bold;")
            inp = QLineEdit(default_val)
            btn = QPushButton("Chọn...")
            btn.setStyleSheet("background: #F8F9FA; border: 1px solid #DEE2E6; padding: 4px 10px; border-radius: 4px;")
            btn.clicked.connect(lambda checked, msg=f"Mở chọn {label_text}": self.stub_action(msg))

            box = QHBoxLayout()
            box.addWidget(inp)
            box.addWidget(btn)

            grid1.addWidget(lbl, row, 0)
            grid1.addLayout(box, row, 1)
            self.path_inputs[label_text] = inp

        layout1.addLayout(grid1)
        layout.addWidget(card1)

        # ------------------- CARD 2: TÙY CHỌN -------------------
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)

        lbl_title2 = QLabel("⚙ Tùy chọn Cảnh & Hiệu ứng")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        row_opt = QHBoxLayout()
        row_opt.addWidget(QLabel("Hiệu ứng (Ảnh tĩnh):"))
        self.cmb_fx = QComboBox()
        self.cmb_fx.addItems(["none", "vừa", "nhẹ", "mạnh"])
        row_opt.addWidget(self.cmb_fx)

        row_opt.addWidget(QLabel(" Fade tiếng (s):"))
        self.spin_fade = QSpinBox()
        self.spin_fade.setValue(4)
        row_opt.addWidget(self.spin_fade)

        row_opt.addWidget(QLabel(" Visualizer:"))
        self.cmb_vis = QComboBox()
        self.cmb_vis.addItems(["none", "bars", "waves"])
        row_opt.addWidget(self.cmb_vis)
        row_opt.addStretch()
        layout2.addLayout(row_opt)

        layout.addWidget(card2)

        # ------------------- 3. ACTION AREA -------------------
        action_layout = QHBoxLayout()
        self.btn_render = QPushButton("🕒 TẠO VIDEO NGỦ")
        self.btn_render.setStyleSheet("background-color: #0066FF; color: white; padding: 12px 24px; font-weight: bold; border-radius: 6px;")
        self.btn_render.clicked.connect(self.run_sleep)

        action_layout.addWidget(self.btn_render)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        layout.addStretch()

    def stub_action(self, msg):
        QMessageBox.information(self, "Thông báo", f"{msg}\n(Tích hợp ở Phase 4/5)")

    def run_sleep(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang chuẩn bị dữ liệu Video Ngủ...", "#D4D4D4")

        # Map UI labels -> config keys for sleep_video.render_sleep_video()
        # UI: fx (none/vừa/nhẹ/mạnh), bgm (ambient path), visualizer
        fx_map = {"none": "none", "vừa": "vua", "nhẹ": "nhe", "mạnh": "nang"}
        cfg = {
            "effect": fx_map.get(self.cmb_fx.currentText(), "rain"),
            "fade": self.spin_fade.value(),
            "viz": self.cmb_vis.currentText(),
            "ambient": self.path_inputs["Âm thanh NỀN (tùy chọn):"].text() or None,
        }
        data = {
            "bg": self.path_inputs["NỀN (clip / ảnh):"].text(),
            "audio": self.path_inputs["AUDIO dài (kịch bản):"].text(),
            "output": self.path_inputs["Xuất ra MP4:"].text(),
            "cfg": cfg,
        }

        self.btn_render.setEnabled(False)
        self.btn_render.setText("⏳ ĐANG TẠO VIDEO NGỦ...")

        self.worker = SleepWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.finished_signal.connect(self.on_sleep_finished)
        self.worker.start()

    def on_sleep_finished(self, success, msg):
        self.btn_render.setEnabled(True)
        self.btn_render.setText("🕒 TẠO VIDEO NGỦ")
        if success:
            QMessageBox.information(self, "Thành công", "Tạo Video Ngủ hoàn tất!")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra:\n{msg}")
