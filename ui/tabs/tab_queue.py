# -*- coding: utf-8 -*-
"""ui.tabs.tab_queue — Hàng đợi (M6b: FIX CRITICAL — job metadata + persistence).

Bug M5: `run_queue()` chỉ truyền text từ QListWidget → QueueWorker bị thiếu cfg/srt/img_dir.

Fix M6:
  1. Lưu song song: QListWidget (UI text) + `self.job_data_list` (list[dict] full).
  2. API `add_job(data_dict)` cho tab khác (Render) push job vào.
  3. `run_queue()` dùng `job_data_list` thay vì parse text.
  4. Persistence: queue.json + history.json (load lúc init, save sau mỗi thay đổi).
  5. Wire buttons: Delete / Clear all / Open history folder / Clear history.
"""
from __future__ import annotations

import json
import os
import sys
import subprocess
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.worker_queue import QueueWorker


# Paths cho persistence — nằm cùng output directory (project root/output)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output")
QUEUE_PATH = os.path.join(_OUTPUT_DIR, "queue.json")
HISTORY_PATH = os.path.join(_OUTPUT_DIR, "history.json")


def _safe_load(path: str) -> list:
    """Load JSON list; trả [] nếu file missing/corrupted."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _safe_save(path: str, data: list) -> bool:
    """Save JSON list. Auto-mkdir parent. Return True nếu OK."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[QueueTab] ERROR saving {path}: {e}", file=sys.stderr)
        return False


class QueueTab(QWidget):
    def __init__(self):
        super().__init__()
        # list[dict] song song với QListWidget — chứa full metadata của mỗi job.
        self.job_data_list: list[dict[str, Any]] = []
        self.history_data: list[dict] = []
        self.setup_ui()
        self._load_state()

    # ---------------------------------------------------------------- UI
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # --- PANEL 1: HÀNG ĐỢI ---
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)

        self.lbl_queue = QLabel("📋 0 video trong hàng đợi")
        self.lbl_queue.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout1.addWidget(self.lbl_queue)

        self.list_queue = QListWidget()
        layout1.addWidget(self.list_queue)

        row_q_btn = QHBoxLayout()
        self.btn_del = QPushButton("Xóa mục chọn")
        self.btn_del.clicked.connect(self._delete_selected)
        self.btn_clear = QPushButton("Xóa hết")
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_render_all = QPushButton("▶ RENDER CẢ HÀNG ĐỢI")
        self.btn_render_all.setStyleSheet(
            "background-color: #0066FF; color: white; padding: 8px 16px;"
            " font-weight: bold; border-radius: 4px;"
        )
        self.btn_render_all.clicked.connect(self.run_queue)

        row_q_btn.addWidget(self.btn_del)
        row_q_btn.addWidget(self.btn_clear)
        row_q_btn.addStretch()
        row_q_btn.addWidget(self.btn_render_all)
        layout1.addLayout(row_q_btn)

        layout.addWidget(card1, 1)

        # --- PANEL 2: LỊCH SỬ ---
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)

        self.lbl_history = QLabel("🕒 Lịch sử render")
        self.lbl_history.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout2.addWidget(self.lbl_history)

        self.table_history = QTableWidget(0, 4)
        self.table_history.setHorizontalHeaderLabels(["Ngày giờ", "Tên file", "Trạng thái", "Ghi chú"])
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout2.addWidget(self.table_history)

        row_h_btn = QHBoxLayout()
        self.btn_open_history = QPushButton("📂 Mở thư mục output")
        self.btn_open_history.clicked.connect(self._open_output_dir)
        self.btn_clear_history = QPushButton("🗑 Xóa lịch sử")
        self.btn_clear_history.clicked.connect(self._clear_history)
        row_h_btn.addWidget(self.btn_open_history)
        row_h_btn.addWidget(self.btn_clear_history)
        row_h_btn.addStretch()
        layout2.addLayout(row_h_btn)

        layout.addWidget(card2, 1)

    # ---------------------------------------------------------------- Persistence
    def _load_state(self):
        """Load queue.json + history.json → populate UI."""
        self.job_data_list = _safe_load(QUEUE_PATH)
        for job in self.job_data_list:
            self._append_job_to_ui(job)

        self.history_data = _safe_load(HISTORY_PATH)
        self._refresh_history_table()
        self._update_count_label()

    def _save_queue(self):
        _safe_save(QUEUE_PATH, self.job_data_list)

    def _save_history(self):
        _safe_save(HISTORY_PATH, self.history_data)

    # ---------------------------------------------------------------- Public API
    def add_job(self, job_dict: dict[str, Any]) -> None:
        """API chuẩn để các tab khác (Render) push job vào hàng đợi.

        `job_dict` cần có: output, srt, img_dir, cfg (xem worker_render.run).
        Optional: voice, scenes, title, channel.
        """
        if not isinstance(job_dict, dict):
            raise TypeError(f"add_job expects dict, got {type(job_dict)}")
        if "output" not in job_dict:
            raise ValueError("add_job requires 'output' key in job_dict")
        # Validate required keys for QueueWorker
        missing = [k for k in ("srt", "img_dir", "cfg") if k not in job_dict]
        if missing:
            raise ValueError(f"add_job missing required keys: {missing}")
        self.job_data_list.append(job_dict)
        self._append_job_to_ui(job_dict)
        self._save_queue()
        self._update_count_label()

    # ---------------------------------------------------------------- UI helpers
    def _append_job_to_ui(self, job: dict):
        """Hiển thị 1 dòng text mô tả job trên QListWidget."""
        title = job.get("title") or job.get("channel") or ""
        prefix = f"[{title}] " if title else ""
        text = f"{prefix}→ {job.get('output', '?')}"
        # Tooltip với full info
        tooltip_lines = [
            f"output: {job.get('output', '?')}",
            f"srt   : {job.get('srt', '?')}",
            f"img   : {job.get('img_dir', '?')}",
        ]
        cfg = job.get("cfg", {})
        if cfg:
            keys = ("aspect", "transition", "color", "sub_mode")
            kv = ", ".join(f"{k}={cfg.get(k, '?')}" for k in keys if k in cfg)
            if kv:
                tooltip_lines.append(f"cfg   : {kv}")
        self.list_queue.addItem(text)
        last = self.list_queue.count() - 1
        self.list_queue.item(last).setToolTip("\n".join(tooltip_lines))

    def _update_count_label(self):
        n = len(self.job_data_list)
        self.lbl_queue.setText(f"📋 {n} video trong hàng đợi" + ("" if n else ""))

    def _refresh_history_table(self):
        self.table_history.setRowCount(0)
        for entry in self.history_data:
            row = self.table_history.rowCount()
            self.table_history.insertRow(row)
            for col, key in enumerate(("timestamp", "output", "status", "note")):
                item = QTableWidgetItem(str(entry.get(key, "")))
                self.table_history.setItem(row, col, item)

    # ---------------------------------------------------------------- Action handlers
    def _delete_selected(self):
        rows = sorted({i.row() for i in self.list_queue.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn job cần xoá trong danh sách.")
            return
        for r in rows:
            if 0 <= r < len(self.job_data_list):
                self.job_data_list.pop(r)
            self.list_queue.takeItem(r)
        self._save_queue()
        self._update_count_label()

    def _clear_all(self):
        if not self.job_data_list:
            QMessageBox.information(self, "Trống", "Hàng đợi đang trống.")
            return
        if QMessageBox.question(
            self, "Xác nhận",
            f"Xoá tất cả {len(self.job_data_list)} job trong hàng đợi?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.job_data_list.clear()
        self.list_queue.clear()
        self._save_queue()
        self._update_count_label()

    def _open_output_dir(self):
        """Mở output/ trong Windows Explorer / macOS Finder / Linux xdg-open."""
        os.makedirs(_OUTPUT_DIR, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(_OUTPUT_DIR)
            elif sys.platform == "darwin":
                subprocess.call(["open", _OUTPUT_DIR])
            else:
                subprocess.call(["xdg-open", _OUTPUT_DIR])
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể mở thư mục: {e}")

    def _clear_history(self):
        if not self.history_data:
            QMessageBox.information(self, "Trống", "Lịch sử đang trống.")
            return
        if QMessageBox.question(
            self, "Xác nhận",
            f"Xoá toàn bộ {len(self.history_data)} mục lịch sử?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.history_data.clear()
        self.table_history.setRowCount(0)
        self._save_history()

    # ---------------------------------------------------------------- RUN
    def run_queue(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang quét hàng đợi...", "#D4D4D4")

        if not self.job_data_list:
            QMessageBox.information(
                self, "Hàng đợi trống",
                "Chưa có video nào trong hàng đợi để render."
            )
            return

        # Validate đủ metadata trước khi chạy (CRITICAL fix)
        bad = []
        for i, job in enumerate(self.job_data_list):
            if not job.get("srt") or not job.get("img_dir"):
                bad.append(i + 1)
        if bad:
            QMessageBox.critical(
                self, "Job không hợp lệ",
                f"Job {bad} thiếu SRT/img_dir. Vui lòng thêm lại từ Render tab."
            )
            return

        # Tạo bản copy để tránh user delete mid-run
        jobs_copy = list(self.job_data_list)
        self.btn_render_all.setEnabled(False)
        self.btn_render_all.setText("⏳ ĐANG CHẠY HÀNG ĐỢI...")

        self.worker = QueueWorker(jobs_copy)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.progress_signal.connect(self.on_queue_progress)
        self.worker.finished_signal.connect(self.on_queue_finished)
        self.worker.start()

    def on_queue_progress(self, idx):
        for i in range(self.list_queue.count()):
            self.list_queue.item(i).setBackground(QColor("#FFFFFF"))
        if 0 <= idx < self.list_queue.count():
            self.list_queue.item(idx).setBackground(QColor("#E3F2FD"))

    def on_queue_finished(self, success, msg):
        self.btn_render_all.setEnabled(True)
        self.btn_render_all.setText("▶ RENDER CẢ HÀNG ĐỢI")

        # Ghi history
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for job in self.job_data_list:
            entry = {
                "timestamp": timestamp,
                "output": job.get("output", ""),
                "status": "OK" if success else "FAIL",
                "note": msg,
            }
            self.history_data.append(entry)
        self._save_history()
        self._refresh_history_table()

        if success:
            QMessageBox.information(self, "Hoàn tất", f"Đã chạy xong hàng đợi: {msg}")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi:\n{msg}")