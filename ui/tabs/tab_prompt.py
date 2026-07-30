# -*- coding: utf-8 -*-
"""ui.tabs.tab_prompt — Tạo Prompt (M6: Auto/Manual pacing + Style Mode + Provider).

M6 additions:
  1. Pacing UX: Auto (target secs) vs Manual (desired scenes count)
  2. Style Mode group: in_prompt / lock_art / lock_all
  3. Provider + Model dropdown (load từ ConfigService)
  4. Đè file warning khi dir trỏ tới nơi đã có veo_prompts.txt
  5. Auto-fill khi thay đổi profile (load text mẫu vào editor tạm)
"""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Qt

from core.worker_prompt import PromptWorker
from services.config_service import ConfigService


# Provider → default model list (sync với tab_settings)
_PROVIDER_MODELS = {
    "gemini":    ["gemini-2.0-flash-exp", "gemini-2.0-flash-thinking-exp",
                  "gemini-2.5-flash", "gemini-2.5-pro"],
    "openai":    ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
    "anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest",
                  "claude-3-opus-latest"],
}


def _load_config() -> dict:
    """Backward-compat helper: load qua ConfigService (M6a)."""
    return ConfigService.instance().load()


class PromptTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = _load_config()
        self.setup_ui()

    def setup_ui(self):
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.scroll.setWidget(self.scroll_content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)

        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ------------------- CARD 1: NGUYÊN LIỆU -------------------
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)

        lbl_title1 = QLabel("📁 Cài đặt Nguyên liệu")
        lbl_title1.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout1.addWidget(lbl_title1)

        grid1 = QGridLayout()
        grid1.setColumnStretch(1, 1)
        grid1.setVerticalSpacing(16)

        # File SRT
        lbl_srt = QLabel("File PHỤ ĐỀ (SRT):")
        lbl_srt.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_srt, 0, 0)
        self.srt_input = QLineEdit("subtitle.srt")
        btn_srt = QPushButton("Chọn...")
        btn_srt.setStyleSheet("background: #F8F9FA; border: 1px solid #DEE2E6; padding: 6px 12px; border-radius: 4px;")
        btn_srt.clicked.connect(self.browse_srt)
        row0 = QHBoxLayout()
        row0.addWidget(self.srt_input)
        row0.addWidget(btn_srt)
        grid1.addLayout(row0, 0, 1)

        # Title
        lbl_title = QLabel("Tiêu đề video:")
        lbl_title.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_title, 1, 0)
        self.title_input = QLineEdit()
        grid1.addWidget(self.title_input, 1, 1)

        # Prompt Dir
        lbl_dir = QLabel("Thư mục lưu prompt:")
        lbl_dir.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_dir, 2, 0)
        self.dir_input = QLineEdit()
        btn_dir = QPushButton("Chọn...")
        btn_dir.setStyleSheet("background: #F8F9FA; border: 1px solid #DEE2E6; padding: 6px 12px; border-radius: 4px;")
        btn_dir.clicked.connect(self.browse_dir)
        row2 = QHBoxLayout()
        row2.addWidget(self.dir_input)
        row2.addWidget(btn_dir)
        grid1.addLayout(row2, 2, 1)

        # Style Profile (load từ ConfigService)
        lbl_profile = QLabel("Style Profile:")
        lbl_profile.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_profile, 3, 0)
        self.profile_combo = QComboBox()
        self._populate_profiles()
        grid1.addWidget(self.profile_combo, 3, 1)

        # Main Character
        lbl_char = QLabel("Tên nhân vật chính:")
        lbl_char.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_char, 4, 0)
        self.char_input = QLineEdit()
        self.char_input.setPlaceholderText("(Trống nếu không có)")
        grid1.addWidget(self.char_input, 4, 1)

        layout1.addLayout(grid1)
        layout.addWidget(card1)

        # ------------------- CARD 2: TÙY CHỌN CHI TIẾT -------------------
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)
        layout2.setSpacing(16)

        lbl_title2 = QLabel("⚙️ Tùy chọn Prompt chi tiết")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        # ----- PACING UX (M6d) — Auto / Manual -----
        pacing_frame = QFrame()
        pacing_frame.setStyleSheet(
            "QFrame { background: #F8F9FA; border-radius: 6px; padding: 8px; }"
        )
        pacing_layout = QVBoxLayout(pacing_frame)
        pacing_layout.setContentsMargins(8, 8, 8, 8)

        lbl_pacing = QLabel("⏱ Pacing (chia cảnh)")
        lbl_pacing.setStyleSheet("font-weight: bold; border: none;")
        pacing_layout.addWidget(lbl_pacing)

        # Auto radio + spinbox
        row_auto = QHBoxLayout()
        self.rad_auto = QRadioButton("🎯 Tự động (nhập thời lượng trung bình / cảnh)")
        self.rad_auto.setChecked(True)
        self.spin_secs = QDoubleSpinBox()
        self.spin_secs.setRange(1.0, 120.0)
        self.spin_secs.setSingleStep(0.5)
        self.spin_secs.setValue(8.0)
        self.spin_secs.setSuffix(" giây")
        self.spin_secs.setFixedWidth(120)
        row_auto.addWidget(self.rad_auto)
        row_auto.addWidget(self.spin_secs)
        row_auto.addStretch()
        pacing_layout.addLayout(row_auto)

        # Manual radio + spinbox
        row_manual = QHBoxLayout()
        self.rad_manual = QRadioButton("📐 Thủ công (nhập tổng số cảnh mong muốn)")
        self.spin_desired_scenes = QSpinBox()
        self.spin_desired_scenes.setRange(1, 999)
        self.spin_desired_scenes.setValue(50)
        self.spin_desired_scenes.setSuffix(" cảnh")
        self.spin_desired_scenes.setFixedWidth(120)
        self.spin_desired_scenes.setEnabled(False)
        row_manual.addWidget(self.rad_manual)
        row_manual.addWidget(self.spin_desired_scenes)
        row_manual.addStretch()
        pacing_layout.addLayout(row_manual)

        # Wire toggled → enable/disable
        self.rad_auto.toggled.connect(self._on_pacing_changed)
        self.rad_manual.toggled.connect(self._on_pacing_changed)

        layout2.addWidget(pacing_frame)

        # ----- STYLE MODE (M6d) — 3 radios -----
        lbl_style = QLabel("🎨 Style Mode (cách đưa style vào prompt):")
        lbl_style.setStyleSheet("font-weight: 500; border: none;")
        layout2.addWidget(lbl_style)

        self.style_mode_group = QButtonGroup(self)
        style_modes = [
            ("📝 Gắn vào prompt (in_prompt)", "in_prompt"),
            ("🔒 Khóa phong cách (lock_art)", "lock_art"),
            ("🔐 Khóa toàn bộ (lock_all)", "lock_all"),
        ]
        for i, (txt, data) in enumerate(style_modes):
            rb = QRadioButton(txt)
            self.style_mode_group.addButton(rb, i)
            layout2.addWidget(rb)
        # Default: in_prompt (khớp legacy behavior)
        self.style_mode_group.button(0).setChecked(True)

        # ----- PROVIDER + MODEL (M6d) -----
        row_prov = QHBoxLayout()
        lbl_prov = QLabel("🏢 Provider:")
        lbl_prov.setStyleSheet("border: none; font-weight: 500;")
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(list(_PROVIDER_MODELS.keys()))
        # Load default provider từ config
        default_prov = self.cfg.get("providers.default_provider", "gemini")
        idx = self.cmb_provider.findText(default_prov)
        if idx >= 0:
            self.cmb_provider.setCurrentIndex(idx)
        self.cmb_provider.currentTextChanged.connect(self._on_provider_changed)
        row_prov.addWidget(lbl_prov)
        row_prov.addWidget(self.cmb_provider)
        row_prov.addStretch()
        layout2.addLayout(row_prov)

        row_model = QHBoxLayout()
        lbl_model = QLabel("🤖 Model:")
        lbl_model.setStyleSheet("border: none; font-weight: 500;")
        self.cmb_model = QComboBox()
        self._refresh_model_list(default_prov)
        row_model.addWidget(lbl_model)
        row_model.addWidget(self.cmb_model)
        row_model.addStretch()
        layout2.addLayout(row_model)

        # ----- PRODUCE MODE (giữ nguyên M2) -----
        lbl_produce = QLabel("Kiểu sản xuất video:")
        lbl_produce.setStyleSheet("border: none; font-weight: 500;")
        layout2.addWidget(lbl_produce)

        self.produce_group = QButtonGroup(self)
        rad_image = QRadioButton("🖼️ Ảnh tĩnh + Ken Burns (1 prompt ẢNH)")
        rad_video = QRadioButton("🎬 Clip video trực tiếp (1 prompt VIDEO)")
        rad_i2v = QRadioButton("⭐ Clip từ ảnh (2 prompt: ẢNH + CHUYỂN ĐỘNG)")
        rad_chain = QRadioButton("🎞️ Ảnh đầu→cuối (chuỗi gối đầu)")
        rad_video.setChecked(True)
        for i, rad in enumerate([rad_image, rad_video, rad_i2v, rad_chain]):
            rad.setStyleSheet("border: none;")
            self.produce_group.addButton(rad, i)
            layout2.addWidget(rad)

        layout.addWidget(card2)

        # ------------------- 3. ACTION AREA -------------------
        action_layout = QHBoxLayout()
        self.btn_create = QPushButton("🤖 TẠO PROMPT (AI)")
        self.btn_create.setStyleSheet(
            "QPushButton { background-color: #0066FF; color: white;"
            " padding: 12px 24px; font-size: 14px; font-weight: bold;"
            " border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #0052CC; }"
        )
        self.btn_create.clicked.connect(self.run_make_prompts)

        self.btn_open = QPushButton("📄 Mở veo_prompts.txt")
        self.btn_open.setStyleSheet(
            "QPushButton { background-color: #E3F2FD; color: #0066FF;"
            " padding: 12px 24px; font-size: 14px; font-weight: bold;"
            " border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #BBDEFB; }"
        )
        self.btn_open.clicked.connect(self.open_prompts)

        action_layout.addWidget(self.btn_create)
        action_layout.addWidget(self.btn_open)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        layout.addStretch()

    # ---------------------------------------------------------------- Helpers
    def refresh_profiles(self):
        """M8: API public để main_window gọi khi profiles thay đổi ở Settings.
        Reload từ ConfigService (file) thay vì self.cfg (cache) để chắc chắn sync.
        """
        fresh = ConfigService.instance().load()
        self.cfg = fresh
        current_selection = self.profile_combo.currentText()
        self._populate_profiles()
        # Cố gắng giữ lại selection nếu vẫn tồn tại
        if current_selection:
            idx = self.profile_combo.findText(current_selection)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        # Refresh luôn model list (nếu user đổi default provider ở Settings)
        prov = fresh.get("providers.default_provider", "gemini")
        if self.cmb_provider.currentText() != prov:
            idx = self.cmb_provider.findText(prov)
            if idx >= 0:
                self.cmb_provider.setCurrentIndex(idx)

    def _populate_profiles(self):
        profiles = self.cfg.get("profiles", {})
        self.profile_combo.clear()
        self.profile_combo.addItems(list(profiles.keys()))

    def _on_pacing_changed(self):
        if self.rad_auto.isChecked():
            self.spin_secs.setEnabled(True)
            self.spin_desired_scenes.setEnabled(False)
        else:
            self.spin_secs.setEnabled(False)
            self.spin_desired_scenes.setEnabled(True)

    def _on_provider_changed(self, provider: str):
        self._refresh_model_list(provider)

    def _refresh_model_list(self, provider: str):
        models = _PROVIDER_MODELS.get(provider, [])
        self.cmb_model.clear()
        self.cmb_model.addItems(models)
        saved = self.cfg.get(f"providers.models.{provider}", "")
        if saved and saved in models:
            self.cmb_model.setCurrentText(saved)

    # ---------------------------------------------------------------- Browse
    def browse_srt(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn file SRT", "",
            "SRT Files (*.srt);;All Files (*.*)"
        )
        if file:
            self.srt_input.setText(file)

    def browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if folder:
            self.dir_input.setText(folder)

    def open_prompts(self):
        """Mở veo_prompts.txt — nếu không có thì thông báo."""
        folder = self.dir_input.text().strip()
        if not folder:
            folder = os.getcwd()
        file_path = os.path.join(folder, "veo_prompts.txt")
        if os.path.exists(file_path):
            try:
                if os.name == "nt":
                    os.startfile(file_path)
                else:
                    import subprocess
                    subprocess.call(["xdg-open", file_path])
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể mở file: {e}")
        else:
            QMessageBox.information(
                self, "Không tìm thấy",
                f"Chưa có file {file_path}.\nVui lòng chạy TẠO PROMPT (AI) trước."
            )

    # ---------------------------------------------------------------- Run
    def _compute_target_secs(self) -> float | None:
        """Tính secs dựa trên Auto/Manual mode.
        Manual mode: cần parse SRT để tính total_dur / desired_scenes.
        """
        if self.rad_auto.isChecked():
            return float(self.spin_secs.value())
        # Manual
        try:
            import auto_edit as ae
            srt_path = self.srt_input.text().strip()
            segs = ae.parse_srt(srt_path)
            if not segs:
                raise ValueError("File SRT rỗng hoặc không hợp lệ")
            total_dur = segs[-1]["end"] - segs[0]["start"]
            n = max(1, self.spin_desired_scenes.value())
            return total_dur / n
        except Exception as e:
            QMessageBox.critical(self, "Lỗi SRT",
                                 f"Không tính được target_secs ở chế độ Thủ công:\n{e}")
            return None

    def _check_overwrite(self) -> bool:
        """Nếu dir đã có veo_prompts.txt -> hỏi user có đè không."""
        folder = self.dir_input.text().strip()
        if not folder:
            return True  # dir rỗng -> chấp nhận (worker sẽ tạo dir cwd)
        existing = os.path.join(folder, "veo_prompts.txt")
        if os.path.isfile(existing):
            ans = QMessageBox.question(
                self, "Đè file cũ?",
                f"Đã có file veo_prompts.txt tại:\n{existing}\n\n"
                f"Bạn có muốn GHI ĐÈ file cũ không?\n"
                f"(Yes = đè, No = đổi thư mục, Cancel = huỷ)",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if ans == QMessageBox.Yes:
                return True
            if ans == QMessageBox.No:
                # Mở lại browse_dir
                self.browse_dir()
                return False
            return False  # Cancel
        return True

    def run_make_prompts(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang chuẩn bị dữ liệu gửi cho AI...", "#D4D4D4")

        # Validate SRT
        srt_path = self.srt_input.text().strip()
        if not srt_path:
            QMessageBox.warning(self, "Thiếu", "Vui lòng chọn file SRT.")
            return
        if not os.path.isfile(srt_path):
            QMessageBox.critical(self, "Lỗi",
                                 f"File SRT không tồn tại:\n{srt_path}")
            return

        # Đè file warning
        if not self._check_overwrite():
            return

        # Tính target_secs
        target_secs = self._compute_target_secs()
        if target_secs is None:
            return

        # Style mode
        checked_style = self.style_mode_group.checkedButton()
        style_mode_data = "in_prompt"
        if checked_style:
            text = checked_style.text()
            for txt, data in [
                ("(in_prompt)", "in_prompt"),
                ("(lock_art)",  "lock_art"),
                ("(lock_all)",  "lock_all"),
            ]:
                if txt in text:
                    style_mode_data = data
                    break

        # Thu thập data
        data = {
            "cfg":          self.cfg,
            "srt":          srt_path,
            "title":        self.title_input.text(),
            "dir":          self.dir_input.text(),
            "profile":      self.profile_combo.currentText(),
            "char":         self.char_input.text(),
            "secs":         target_secs,
            "produce_mode": self.produce_group.checkedButton().text() if self.produce_group.checkedButton() else "",
            "style_mode":   style_mode_data,
            "provider":     self.cmb_provider.currentText(),
            "model":        self.cmb_model.currentText(),
        }

        # Persist provider default để lần sau còn nhớ
        self.cfg.set("providers.default_provider", data["provider"], auto_save=True)
        self.cfg.set(f"providers.models.{data['provider']}", data["model"], auto_save=True)

        self.btn_create.setEnabled(False)
        self.btn_create.setText("⏳ ĐANG TẠO PROMPT...")
        self.worker = PromptWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.finished_signal.connect(self.on_prompt_finished)
        self.worker.start()

    def on_prompt_finished(self, success, msg):
        self.btn_create.setEnabled(True)
        self.btn_create.setText("🤖 TẠO PROMPT (AI)")
        if success:
            QMessageBox.information(self, "Thành công", "Tạo Prompt hoàn tất!")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra:\n{msg}")