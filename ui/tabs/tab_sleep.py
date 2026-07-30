# -*- coding: utf-8 -*-
"""ui.tabs.tab_sleep — Video Ngủ Tab (M7: Feature Parity 100%).

M7 — nâng cấp từ stub UI lên full wiring:
  - 2 combobox thật: cmb_effect (5 effect) + cmb_intensity (3 mức)
  - 16 options: noise, vignette + 2 spinbox, aspect, fps, max_seconds, item_sec,
                ambient_volume, encoder, viz, fade
  - Branding group: title text, intro/outro paths, logo path + position
  - 7 browse handlers thật (QFileDialog) thay cho stub_action()
  - Pass toàn bộ xuống SleepWorker → sleep_video.render_sleep_video(cfg)
"""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QScrollArea,
)

from core.worker_sleep import SleepWorker


# ---- Danh sách key cho combos (sync với sleep_video.EFFECTS / INTENSITIES) ----
EFFECTS = [
    ("Không (None)", "none"),
    ("🌧 Mưa (Rain)", "rain"),
    ("❄ Tuyết (Snow)", "snow"),
    ("🌫 Sương mù (Fog)", "fog"),
    ("✨ Bokeh (Bokeh)", "bokeh"),
]
INTENSITIES = [
    ("Nhẹ", "nhe"),
    ("Vừa", "vua"),
    ("Nặng", "nang"),
]
ASPECTS = [
    ("Tự động (legacy)", None),
    ("16:9 ngang (1920x1080)", "16:9"),
    ("9:16 dọc (1080x1920)", "9:16"),
    ("1:1 vuông (1080x1080)", "1:1"),
]
FPS_OPTIONS = [
    ("30 fps (legacy mặc định)", 30),
    ("24 fps (điện ảnh)", 24),
    ("60 fps (mượt)", 60),
]
ENCODERS = [
    ("Tự động (auto — GPU nếu có)", "auto"),
    ("CPU (libx264, chậm nhưng ổn định)", "cpu"),
]
VISUALIZERS = [
    ("Không (None)", "none"),
    ("▮ Thanh nhạc (bars)", "bars"),
    ("〰 Sóng âm (waves)", "waves"),
]
LOGO_POSITIONS = [
    ("Góc trên trái", "topleft"),
    ("Góc trên phải", "topright"),
    ("Góc dưới trái", "bottomleft"),
    ("Góc dưới phải", "bottomright"),
    ("Chính giữa", "center"),
]


class SleepTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # ScrollArea để 16 options không bị cắt ở màn hình nhỏ
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

        # ===========================================================
        # CARD 1: FILE PATHS (bg, audio, ambient, output, intro/outro/logo)
        # ===========================================================
        card1 = QFrame()
        card1.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }"
        )
        layout1 = QVBoxLayout(card1)

        lbl_title1 = QLabel("📁 Khu vực Đầu vào File (Video ngủ dài 3-4 tiếng)")
        lbl_title1.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout1.addWidget(lbl_title1)

        grid1 = QGridLayout()
        grid1.setColumnStretch(1, 1)
        grid1.setVerticalSpacing(12)

        # Build input rows with Browse buttons (state bound to handler dict)
        self.path_inputs = {}      # label -> QLineEdit
        self.browse_handlers = {}  # label -> callable

        # ---- Row 0: NỀN (file hoặc folder) ----
        self._add_path_row(grid1, 0, "NỀN (clip / ảnh / folder):",
                           default="backgrounds", browse_filter="",
                           browse_func=self.browse_bg)
        # ---- Row 1: AUDIO dài ----
        self._add_path_row(grid1, 1, "AUDIO dài (kịch bản):",
                           default="", browse_filter="Audio (*.mp3 *.wav *.m4a *.aac *.flac)",
                           browse_func=self.browse_audio)
        # ---- Row 2: Âm thanh nền (mưa/gió/tuyết) ----
        self._add_path_row(grid1, 2, "Âm thanh NỀN (tùy chọn):",
                           default="", browse_filter="Audio (*.mp3 *.wav *.m4a)",
                           browse_func=self.browse_ambient)
        # ---- Row 3: Intro (M7 branding) ----
        self._add_path_row(grid1, 3, "Intro (M7 — video mở đầu):",
                           default="", browse_filter="Video (*.mp4 *.mov *.mkv)",
                           browse_func=self.browse_intro)
        # ---- Row 4: Outro (M7 branding) ----
        self._add_path_row(grid1, 4, "Outro (M7 — video kết thúc):",
                           default="", browse_filter="Video (*.mp4 *.mov *.mkv)",
                           browse_func=self.browse_outro)
        # ---- Row 5: Logo (M7 branding) ----
        self._add_path_row(grid1, 5, "Logo (M7 — PNG overlay):",
                           default="", browse_filter="Image (*.png *.svg *.jpg)",
                           browse_func=self.browse_logo)
        # ---- Row 6: Output ----
        self._add_path_row(grid1, 6, "Xuất ra MP4:", default="output/sleep.mp4",
                           browse_filter="MP4 Video (*.mp4)",
                           save_mode=True, browse_func=self.browse_output)

        layout1.addLayout(grid1)
        layout.addWidget(card1)

        # ===========================================================
        # CARD 2: HIỆU ỨNG (effect + intensity + visualizer)
        # ===========================================================
        card2 = QFrame()
        card2.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }"
        )
        layout2 = QVBoxLayout(card2)
        layout2.setSpacing(16)

        lbl_title2 = QLabel("🎨 Hiệu ứng")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        grid2 = QGridLayout()
        grid2.setColumnStretch(1, 1)
        grid2.setVerticalSpacing(12)

        # Effect (M7.1)
        grid2.addWidget(QLabel("Loại hiệu ứng:"), 0, 0)
        self.cmb_effect = QComboBox()
        for label, data in EFFECTS:
            self.cmb_effect.addItem(label, data)
        grid2.addWidget(self.cmb_effect, 0, 1)

        # Intensity (M7.1)
        grid2.addWidget(QLabel("Cường độ:"), 1, 0)
        self.cmb_intensity = QComboBox()
        for label, data in INTENSITIES:
            self.cmb_intensity.addItem(label, data)
        self.cmb_intensity.setCurrentIndex(1)  # default "Vừa"
        grid2.addWidget(self.cmb_intensity, 1, 1)

        # Visualizer
        grid2.addWidget(QLabel("Visualizer âm thanh:"), 2, 0)
        self.cmb_vis = QComboBox()
        for label, data in VISUALIZERS:
            self.cmb_vis.addItem(label, data)
        grid2.addWidget(self.cmb_vis, 2, 1)

        # Fade tiếng
        grid2.addWidget(QLabel("Fade tiếng (s):"), 3, 0)
        self.spin_fade = QDoubleSpinBox()
        self.spin_fade.setRange(0.0, 30.0)
        self.spin_fade.setSingleStep(0.5)
        self.spin_fade.setValue(4.0)
        grid2.addWidget(self.spin_fade, 3, 1)

        layout2.addLayout(grid2)
        layout.addWidget(card2)

        # ===========================================================
        # CARD 3: TÙY CHỌN NÂNG CAO (16 options M7)
        # ===========================================================
        card3 = QFrame()
        card3.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }"
        )
        layout3 = QVBoxLayout(card3)
        layout3.setSpacing(16)

        lbl_title3 = QLabel("⚙ Tùy chọn Nâng cao (16 options M7)")
        lbl_title3.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout3.addWidget(lbl_title3)

        grid3 = QGridLayout()
        grid3.setColumnStretch(1, 1)
        grid3.setVerticalSpacing(12)

        row = 0
        # --- Aspect ratio ---
        grid3.addWidget(QLabel("Tỉ lệ khung hình:"), row, 0)
        self.cmb_aspect = QComboBox()
        for label, data in ASPECTS:
            self.cmb_aspect.addItem(label, data)
        grid3.addWidget(self.cmb_aspect, row, 1)
        row += 1

        # --- FPS override ---
        grid3.addWidget(QLabel("FPS:"), row, 0)
        self.cmb_fps = QComboBox()
        for label, data in FPS_OPTIONS:
            self.cmb_fps.addItem(label, data)
        grid3.addWidget(self.cmb_fps, row, 1)
        row += 1

        # --- Max seconds (giới hạn tổng độ dài) ---
        grid3.addWidget(QLabel("Giới hạn tối đa (giây):"), row, 0)
        self.spin_max_seconds = QSpinBox()
        self.spin_max_seconds.setRange(0, 36000)
        self.spin_max_seconds.setSingleStep(60)
        self.spin_max_seconds.setValue(0)
        self.spin_max_seconds.setSpecialValueText("Không giới hạn")
        grid3.addWidget(self.spin_max_seconds, row, 1)
        row += 1

        # --- Item sec (số giây mỗi mục nếu bg là folder) ---
        grid3.addWidget(QLabel("Số giây / mục nền:"), row, 0)
        self.spin_item_sec = QSpinBox()
        self.spin_item_sec.setRange(4, 3600)
        self.spin_item_sec.setSingleStep(5)
        self.spin_item_sec.setValue(20)
        grid3.addWidget(self.spin_item_sec, row, 1)
        row += 1

        # --- Ambient volume (0.0 - 2.0) ---
        grid3.addWidget(QLabel("Âm lượng âm thanh nền (0-2):"), row, 0)
        self.spin_ambient_vol = QDoubleSpinBox()
        self.spin_ambient_vol.setRange(0.0, 2.0)
        self.spin_ambient_vol.setSingleStep(0.05)
        self.spin_ambient_vol.setValue(0.25)
        self.spin_ambient_vol.setDecimals(2)
        grid3.addWidget(self.spin_ambient_vol, row, 1)
        row += 1

        # --- Encoder ---
        grid3.addWidget(QLabel("Encoder:"), row, 0)
        self.cmb_encoder = QComboBox()
        for label, data in ENCODERS:
            self.cmb_encoder.addItem(label, data)
        grid3.addWidget(self.cmb_encoder, row, 1)
        row += 1

        # --- Noise filter ---
        grid3.addWidget(QLabel("Hiệu ứng nhiễu:"), row, 0)
        self.chk_noise = QCheckBox("Thêm noise (ffmpeg noise=alls=20:allf=t+u)")
        grid3.addWidget(self.chk_noise, row, 1)
        row += 1

        # --- Vignette checkbox ---
        grid3.addWidget(QLabel("Vignette (tối 4 góc):"), row, 0)
        self.chk_vignette = QCheckBox("Bật vignette")
        grid3.addWidget(self.chk_vignette, row, 1)
        row += 1

        # --- Vignette Intensity (0-1) ---
        grid3.addWidget(QLabel("Vignette intensity (0-1):"), row, 0)
        self.spin_vintensity = QDoubleSpinBox()
        self.spin_vintensity.setRange(0.0, 1.0)
        self.spin_vintensity.setSingleStep(0.05)
        self.spin_vintensity.setValue(0.5)
        self.spin_vintensity.setDecimals(2)
        grid3.addWidget(self.spin_vintensity, row, 1)
        row += 1

        # --- Vignette Strength (0-1) ---
        grid3.addWidget(QLabel("Vignette strength (0-1):"), row, 0)
        self.spin_vistrength = QDoubleSpinBox()
        self.spin_vistrength.setRange(0.0, 1.0)
        self.spin_vistrength.setSingleStep(0.05)
        self.spin_vistrength.setValue(0.5)
        self.spin_vistrength.setDecimals(2)
        grid3.addWidget(self.spin_vistrength, row, 1)
        row += 1

        layout3.addLayout(grid3)
        layout.addWidget(card3)

        # ===========================================================
        # CARD 4: BRANDING (M7 - title / intro / outro / logo position)
        # ===========================================================
        card4 = QFrame()
        card4.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }"
        )
        layout4 = QVBoxLayout(card4)
        layout4.setSpacing(16)

        lbl_title4 = QLabel("🏷 Branding (M7 — title + intro/outro/logo)")
        lbl_title4.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout4.addWidget(lbl_title4)

        grid4 = QGridLayout()
        grid4.setColumnStretch(1, 1)
        grid4.setVerticalSpacing(12)

        # Title (text)
        grid4.addWidget(QLabel("Title (burn-in 5s đầu):"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("VD: Video Ngủ 4 Tiếng — Relaxing")
        grid4.addWidget(self.title_input, 0, 1)

        # Logo position
        grid4.addWidget(QLabel("Vị trí logo:"), 1, 0)
        self.cmb_logo_pos = QComboBox()
        for label, data in LOGO_POSITIONS:
            self.cmb_logo_pos.addItem(label, data)
        self.cmb_logo_pos.setCurrentIndex(1)  # default topright
        grid4.addWidget(self.cmb_logo_pos, 1, 1)

        layout4.addLayout(grid4)
        layout.addWidget(card4)

        # ===========================================================
        # ACTION AREA
        # ===========================================================
        action_layout = QHBoxLayout()
        self.btn_render = QPushButton("🕒 TẠO VIDEO NGỦ")
        self.btn_render.setStyleSheet(
            "QPushButton { background-color: #0066FF; color: white;"
            " padding: 12px 24px; font-size: 14px; font-weight: bold;"
            " border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #0052CC; }"
        )
        self.btn_render.clicked.connect(self.run_sleep)

        self.btn_open = QPushButton("📂 Mở file Output")
        self.btn_open.setStyleSheet(
            "QPushButton { background-color: #E3F2FD; color: #0066FF;"
            " padding: 12px 24px; font-size: 14px; font-weight: bold;"
            " border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #BBDEFB; }"
        )
        self.btn_open.clicked.connect(self.open_output)

        action_layout.addWidget(self.btn_render)
        action_layout.addWidget(self.btn_open)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        layout.addStretch()

    # ===============================================================
    # Helper — add row to grid with label + QLineEdit + Browse button
    # ===============================================================
    def _add_path_row(self, grid, row, label_text, default="", browse_filter="",
                      save_mode=False, browse_func=None):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("border: none; font-weight: 500;")
        inp = QLineEdit(default)
        btn = QPushButton("Chọn...")
        btn.setStyleSheet(
            "background: #F8F9FA; border: 1px solid #DEE2E6;"
            " padding: 4px 12px; border-radius: 4px;"
        )
        if browse_func:
            btn.clicked.connect(lambda: browse_func())

        box = QHBoxLayout()
        box.addWidget(inp)
        box.addWidget(btn)

        grid.addWidget(lbl, row, 0)
        grid.addLayout(box, row, 1)
        self.path_inputs[label_text] = inp
        if browse_func:
            self.browse_handlers[label_text] = browse_func

    # ===============================================================
    # Browse handlers — QFileDialog thật, xóa stub_action()
    # ===============================================================
    def browse_bg(self):
        """Background: cho phép chọn FILE hoặc FOLDER nhiều ảnh/clip."""
        # Tab path input tương ứng
        inp = self.path_inputs["NỀN (clip / ảnh / folder):"]
        start = inp.text() or os.getcwd()
        # Thử file trước
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn file nền (ảnh/clip)", start,
            "Media (*.mp4 *.mov *.mkv *.jpg *.jpeg *.png);;All Files (*.*)"
        )
        if file:
            inp.setText(file)
            return
        # Nếu không chọn file, cho phép chọn folder
        folder = QFileDialog.getExistingDirectory(self, "Hoặc chọn folder chứa nhiều ảnh/clip", start)
        if folder:
            inp.setText(folder)

    def browse_audio(self):
        inp = self.path_inputs["AUDIO dài (kịch bản):"]
        start = inp.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Audio", start,
            "Audio (*.mp3 *.wav *.m4a *.aac *.flac);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    def browse_ambient(self):
        inp = self.path_inputs["Âm thanh NỀN (tùy chọn):"]
        start = inp.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn âm thanh nền (mưa/gió/tuyết)", start,
            "Audio (*.mp3 *.wav *.m4a);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    def browse_intro(self):
        inp = self.path_inputs["Intro (M7 — video mở đầu):"]
        start = inp.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn video Intro", start,
            "Video (*.mp4 *.mov *.mkv);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    def browse_outro(self):
        inp = self.path_inputs["Outro (M7 — video kết thúc):"]
        start = inp.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn video Outro", start,
            "Video (*.mp4 *.mov *.mkv);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    def browse_logo(self):
        inp = self.path_inputs["Logo (M7 — PNG overlay):"]
        start = inp.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Logo (PNG/SVG)", start,
            "Image (*.png *.svg *.jpg);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    def browse_output(self):
        inp = self.path_inputs["Xuất ra MP4:"]
        start = inp.text() or "sleep.mp4"
        file, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Output", start,
            "MP4 Video (*.mp4);;All Files (*.*)"
        )
        if file:
            inp.setText(file)

    # ===============================================================
    # Action — open output file
    # ===============================================================
    def open_output(self):
        out_path = self.path_inputs["Xuất ra MP4:"].text().strip()
        if not out_path:
            QMessageBox.information(self, "Chưa có", "Vui lòng chọn đường dẫn Output trước.")
            return
        if not os.path.isfile(out_path):
            QMessageBox.information(
                self, "Chưa có file",
                f"File chưa tồn tại:\n{out_path}\n\n"
                f"Hãy bấm TẠO VIDEO NGỦ trước."
            )
            return
        try:
            if os.name == "nt":
                os.startfile(out_path)
            else:
                import subprocess
                subprocess.call(["xdg-open", out_path])
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể mở file: {e}")

    # ===============================================================
    # Run — mapping UI → cfg → SleepWorker
    # ===============================================================
    def _get_path(self, label: str) -> str:
        """Đọc path từ input theo label, strip, trả về '' nếu trống."""
        inp = self.path_inputs.get(label)
        return inp.text().strip() if inp else ""

    def _collect_cfg(self) -> dict:
        """Thu thập toàn bộ config từ UI → dict đúng schema của sleep_video.render_sleep_video."""
        return {
            # ----- Effect chain (M7.1: tách 2 combo) -----
            "effect":     self.cmb_effect.currentData() or "none",
            "intensity":  self.cmb_intensity.currentData() or "vua",
            "viz":        self.cmb_vis.currentData() or "none",
            "fade":       self.spin_fade.value(),

            # ----- Audio & bg -----
            "ambient":          self._get_path("Âm thanh NỀN (tùy chọn):") or None,
            "ambient_volume":   self.spin_ambient_vol.value(),

            # ----- Render constraints (M7 — 16 options) -----
            "max_seconds":      self.spin_max_seconds.value() or None,
            "item_sec":         self.spin_item_sec.value(),
            "encoder":          self.cmb_encoder.currentData() or "auto",
            "aspect":           self.cmb_aspect.currentData(),   # None = legacy
            "fps":              self.cmb_fps.currentData(),      # None = legacy
            "noise":            self.chk_noise.isChecked(),
            "vignette":         self.chk_vignette.isChecked(),
            "vignette_intensity": self.spin_vintensity.value(),
            "vignette_strength":  self.spin_vistrength.value(),

            # ----- Branding (M7) -----
            "title":         self.title_input.text().strip() or None,
            "intro":         self._get_path("Intro (M7 — video mở đầu):") or None,
            "outro":         self._get_path("Outro (M7 — video kết thúc):") or None,
            "logo":          self._get_path("Logo (M7 — PNG overlay):") or None,
            "logo_position": self.cmb_logo_pos.currentData() or "topright",
        }

    def _validate(self) -> bool:
        """Validate trước khi chạy worker. Trả True nếu OK."""
        bg = self._get_path("NỀN (clip / ảnh / folder):")
        audio = self._get_path("AUDIO dài (kịch bản):")
        out = self._get_path("Xuất ra MP4:")

        if not bg:
            QMessageBox.warning(self, "Thiếu NỀN",
                                "Vui lòng chọn file/folder nền (ảnh hoặc clip).")
            return False
        if not os.path.isfile(bg) and not os.path.isdir(bg):
            QMessageBox.critical(self, "NỀN không tồn tại",
                                 f"Không tìm thấy file/folder:\n{bg}")
            return False
        if not audio:
            QMessageBox.warning(self, "Thiếu AUDIO",
                                "Vui lòng chọn file audio dài.")
            return False
        if not os.path.isfile(audio):
            QMessageBox.critical(self, "AUDIO không tồn tại",
                                 f"Không tìm thấy file:\n{audio}")
            return False
        if not out:
            QMessageBox.warning(self, "Thiếu Output",
                                "Vui lòng nhập đường dẫn file MP4 xuất ra.")
            return False

        # Validate optional branding paths
        for label, fmt in [
            ("Intro (M7 — video mở đầu):", "Video"),
            ("Outro (M7 — video kết thúc):", "Video"),
            ("Logo (M7 — PNG overlay):", "Logo"),
        ]:
            p = self._get_path(label)
            if p and not os.path.isfile(p):
                QMessageBox.critical(
                    self, f"{fmt} không tồn tại",
                    f"Đường dẫn {label} không hợp lệ:\n{p}"
                )
                return False
        return True

    def run_sleep(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang chuẩn bị dữ liệu Video Ngủ (M7)...", "#D4D4D4")

        if not self._validate():
            return

        cfg = self._collect_cfg()

        data = {
            "bg":     self._get_path("NỀN (clip / ảnh / folder):"),
            "audio":  self._get_path("AUDIO dài (kịch bản):"),
            "output": self._get_path("Xuất ra MP4:"),
            "cfg":    cfg,
        }

        # Summary log
        if hasattr(main_win, "append_log"):
            main_win.append_log(
                f"• effect={cfg['effect']}/{cfg['intensity']} | viz={cfg['viz']} | "
                f"encoder={cfg['encoder']} | aspect={cfg['aspect']} | fps={cfg['fps']}",
                "#D4D4D4",
            )
            branding = []
            if cfg["title"]: branding.append(f"title='{cfg['title']}'")
            if cfg["intro"]: branding.append("intro")
            if cfg["outro"]: branding.append("outro")
            if cfg["logo"]:  branding.append(f"logo@{cfg['logo_position']}")
            if cfg["noise"]: branding.append("noise")
            if cfg["vignette"]: branding.append("vignette")
            if branding:
                main_win.append_log(f"• Branding/filters: {', '.join(branding)}", "#28A745")

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