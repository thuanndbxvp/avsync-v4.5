# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from core.worker_queue import QueueWorker

class QueueTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # --- PANEL 1: HÀNG ĐỢI ---
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)

        lbl_queue = QLabel("📋 0 video trong hàng đợi")
        lbl_queue.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout1.addWidget(lbl_queue)

        self.list_queue = QListWidget()
        self.list_queue.addItem("Chưa có video nào trong hàng đợi.")
        layout1.addWidget(self.list_queue)

        row_q_btn = QHBoxLayout()
        btn_del = QPushButton("Xóa mục chọn")
        btn_clear = QPushButton("Xóa hết")
        self.btn_render_all = QPushButton("▶ RENDER CẢ HÀNG ĐỢI")
        self.btn_render_all.setStyleSheet("background-color: #0066FF; color: white; padding: 8px 16px; font-weight: bold; border-radius: 4px;")

        for btn in [btn_del, btn_clear]:
            btn.clicked.connect(lambda checked, text=btn.text(): self.stub_action(f"Bấm: {text}"))

        self.btn_render_all.clicked.connect(self.run_queue)

        row_q_btn.addWidget(btn_del)
        row_q_btn.addWidget(btn_clear)
        row_q_btn.addStretch()
        row_q_btn.addWidget(self.btn_render_all)
        layout1.addLayout(row_q_btn)

        layout.addWidget(card1, 1)

        # --- PANEL 2: LỊCH SỬ ---
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)

        lbl_history = QLabel("🕒 Lịch sử render")
        lbl_history.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout2.addWidget(lbl_history)

        self.table_history = QTableWidget(0, 2)
        self.table_history.setHorizontalHeaderLabels(["Ngày giờ", "Tên file"])
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout2.addWidget(self.table_history)

        row_h_btn = QHBoxLayout()
        btn_open = QPushButton("Mở thư mục")
        btn_clear_h = QPushButton("Xóa lịch sử")

        for btn in [btn_open, btn_clear_h]:
            btn.clicked.connect(lambda checked, text=btn.text(): self.stub_action(f"Bấm: {text}"))
            row_h_btn.addWidget(btn)
        row_h_btn.addStretch()
        layout2.addLayout(row_h_btn)

        layout.addWidget(card2, 1)

    def stub_action(self, msg):
        QMessageBox.information(self, "Thông báo", f"{msg}\n(Backend chờ Tích hợp)")

    def run_queue(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang quét hàng đợi...", "#D4D4D4")

        # Thu thập items từ QListWidget (skip placeholder)
        jobs = []
        for i in range(self.list_queue.count()):
            item_text = self.list_queue.item(i).text()
            if "Chưa có video" in item_text:
                continue
            jobs.append({"output": item_text, "id": i})

        if not jobs:
            QMessageBox.information(self, "Hàng đợi trống", "Chưa có video nào trong hàng đợi để render.")
            return

        self.btn_render_all.setEnabled(False)
        self.btn_render_all.setText("⏳ ĐANG CHẠY HÀNG ĐỢI...")

        self.worker = QueueWorker(jobs)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.progress_signal.connect(self.on_queue_progress)
        self.worker.finished_signal.connect(self.on_queue_finished)
        self.worker.start()

    def on_queue_progress(self, idx):
        # Highlight item đang chạy
        for i in range(self.list_queue.count()):
            self.list_queue.item(i).setBackground(QListWidget().palette().window()) # reset
        if idx < self.list_queue.count():
            from PySide6.QtGui import QColor
            self.list_queue.item(idx).setBackground(QColor("#E3F2FD"))

    def on_queue_finished(self, success, msg):
        self.btn_render_all.setEnabled(True)
        self.btn_render_all.setText("▶ RENDER CẢ HÀNG ĐỢI")
        if success:
            QMessageBox.information(self, "Hoàn tất", f"Đã chạy xong hàng đợi: {msg}")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi:\n{msg}")
