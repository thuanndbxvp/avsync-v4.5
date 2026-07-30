# -*- coding: utf-8 -*-
"""ui.tabs.tab_render — Render Video Tab (Milestone 5: Feature Parity với legacy).

Các thẻ (Card):
  1. Nguyên liệu & Hồ sơ — 5 path inputs (SRT/img_dir/voice/scenes_csv/output) + channel select
  2. Tuỳ chọn ghép     — aspect/transition/crossfade/Ken Burns/sub/font/size
  3. Phụ đề chuyên sâu — mode (word/line/kara) + font size quick + màu chữ + màu viền + font
  4. Màu phim & FX     — preset màu (cinematic/cold/warm/bw/none) + vignette + grain + title text
  5. Âm thanh          — BGM + SFX + 3 volume spin + ducking + keep clip audio
  6. Branding          — Logo + Intro + Outro + 4 vị trí logo + 3 kiểu logo + opacity

WIRE:
  - "Chọn..." button -> mở QFileDialog (file hoặc directory tuỳ ngữ nghĩa)
  - `run_render()` map TOÀN BỘ cfg keys → truyền nguyên sang `core.worker_render` (M3 shim).
"""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QRadioButton, QButtonGroup, QFileDialog,
    QMessageBox, QScrollArea, QCheckBox, QDoubleSpinBox,
    QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.worker_render import RenderWorker
from ui.widgets.color_button import ColorButton


# ----------------------------------------------------------------------------
# Constants — khớp CLI choices của auto_edit._legacy_main()
# ----------------------------------------------------------------------------
ASPECTS = ["16:9", "9:16"]
IMAGE_MODES = [
    ("Tự động (auto)", "auto"),
    ("1 ảnh / 1 đoạn phụ đề (srt)", "srt"),
    ("Rải đều N ảnh (spread)", "spread"),
]
CLIP_FITS = [
    ("Tự động (auto)", "auto"),
    ("Speed (đổi tốc độ về Veo)", "speed"),
    ("Cut (cắt khít)", "cut"),
    ("Loop (lặp)", "loop"),
]
# Đồng bộ với auto_edit.TRANSITIONS — chỉ lấy phổ biến cho dropdown
TRANSITIONS = [
    "none", "fade", "fadeblack", "fadewhite", "dissolve",
    "slideleft", "slideright", "slideup", "slidedown",
    "circleopen", "circleclose", "radial", "pixelize", "zoomin",
]
SUB_MODES = [
    ("1 TỪ nhảy theo voice", "word"),
    ("Cả câu", "line"),
    ("Cả câu + tô màu karaoke", "kara"),
]
COLORS = [
    ("Không (none)", "none"),
    ("Cinematic", "cinematic"),
    ("Lạnh (Cold)", "cold"),
    ("Ấm (Warm)", "warm"),
    ("Đen trắng (BW)", "bw"),
]
LOGO_POS = [
    ("Trên-trái (tl)", "tl"),
    ("Trên-phải (tr)", "tr"),
    ("Dưới-trái (bl)", "bl"),
    ("Dưới-phải (br)", "br"),
]
LOGO_SHAPES = [
    ("Vuông (square)", "square"),
    ("Bo góc mềm (round)", "round"),
    ("Tròn avatar (circle)", "circle"),
]


def _card_style():
    return (
        "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6;"
        " border-radius: 8px; }"
    )


def _title_style():
    return "font-size: 16px; font-weight: bold; color: #191B24; border: none;"


def _label_style():
    return "border: none; font-weight: 500;"


def _btn_choose_style():
    return (
        "background: #F8F9FA; border: 1px solid #DEE2E6; padding: 4px 10px;"
        " border-radius: 4px;"
    )


class RenderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.path_inputs: dict[str, QLineEdit] = {}
        self._setup_ui()

    # ---------------------------------------------------------------- UI
    def _setup_ui(self):
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll.setWidget(self.scroll_content)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(self.scroll)

        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        layout.addWidget(self._card_nguyen_lieu())
        layout.addWidget(self._card_ghep_video())
        layout.addWidget(self._card_phu_de())
        layout.addWidget(self._card_mau_fx())
        layout.addWidget(self._card_am_thanh())
        layout.addWidget(self._card_branding())

        # Action row
        act = QHBoxLayout()
        self.btn_render = QPushButton("▶ RENDER VIDEO")
        self.btn_preview = QPushButton("👁 Xem trước (1 cảnh)")
        self.btn_queue = QPushButton("➕ Thêm Hàng đợi")
        self.btn_render.setStyleSheet(
            "QPushButton { background-color: #0066FF; color: white; padding: 12px 24px;"
            " font-weight: bold; border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #0052CC; }"
        )
        for btn in [self.btn_preview, self.btn_queue]:
            btn.setStyleSheet(
                "QPushButton { background-color: #E3F2FD; color: #0066FF;"
                " padding: 10px 16px; font-weight: bold; border-radius: 6px; border: none; }"
                "QPushButton:hover { background-color: #BBDEFB; }"
            )
        act.addWidget(self.btn_render)
        act.addWidget(self.btn_preview)
        act.addWidget(self.btn_queue)
        act.addStretch()
        layout.addLayout(act)
        layout.addStretch()

        # Wire signals
        self.btn_render.clicked.connect(self.run_render)
        self.btn_preview.clicked.connect(self.run_preview)
        self.btn_queue.clicked.connect(self.run_queue_add)

    # -------------------------------------------------------- Card 1
    def _card_nguyen_lieu(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        # Channel row
        row_ch = QHBoxLayout()
        lbl = QLabel("📺 Hồ sơ kênh:")
        lbl.setStyleSheet(_label_style())
        self.cmb_channel = QComboBox()
        self.cmb_channel.setEditable(True)
        self.cmb_channel.setFixedWidth(200)
        btn_save = QPushButton("💾 Lưu kênh...")
        btn_save.setStyleSheet(_btn_choose_style())
        btn_del = QPushButton("🗑")
        btn_del.setStyleSheet(_btn_choose_style())
        row_ch.addWidget(lbl)
        row_ch.addWidget(self.cmb_channel)
        row_ch.addWidget(btn_save)
        row_ch.addWidget(btn_del)
        row_ch.addStretch()
        v.addLayout(row_ch)

        # 5 path rows
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setVerticalSpacing(12)
        grid.setContentsMargins(0, 8, 0, 0)

        # (label, default text, browse kind)
        #   kind: "file"=QFileDialog.getOpenFileName; "dir"=getExistingDirectory; "save"=getSaveFileName; "" = no browse
        inputs = [
            ("File PHỤ ĐỀ (SRT):",       "input/subtitle.srt", "file"),
            ("Thư mục ẢNH/CLIP:",        "input/images",       "dir"),
            ("File VOICEOVER:",           "",                   "file"),
            ("📋 File bảng cảnh (CSV):", "",                   "file"),
            ("🎬 Video intro (tuỳ chọn):", "",                  "file"),
            ("🏁 Video outro (tuỳ chọn):", "",                  "file"),
            ("🎵 Nhạc nền - BGM:",        "",                   "file"),
            ("💥 SFX chuyển cảnh:",       "",                   "file"),
            ("💧 Logo/Watermark:",        "",                   "file"),
            ("Xuất ra MP4:",              "output/final.mp4",   "save"),
        ]
        self.path_inputs = {}
        for row, (label_text, default_val, kind) in enumerate(inputs):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(_label_style())
            inp = QLineEdit(default_val)
            btn = QPushButton("Chọn...")
            btn.setStyleSheet(_btn_choose_style())
            btn.clicked.connect(lambda checked, lt=label_text, k=kind: self._browse(lt, k))

            h = QHBoxLayout()
            h.addWidget(inp)
            h.addWidget(btn)

            grid.addWidget(lbl, row, 0)
            grid.addLayout(h, row, 1)
            self.path_inputs[label_text] = inp

        v.addLayout(grid)
        return card

    def _browse(self, label_text: str, kind: str):
        """Browse file/dir thật — thay cho stub cũ."""
        inp = self.path_inputs.get(label_text)
        if inp is None:
            return
        start_dir = inp.text() or os.getcwd()
        if kind == "file":
            path, _ = QFileDialog.getOpenFileName(self, f"Chọn {label_text}", start_dir)
            if path:
                inp.setText(path)
        elif kind == "dir":
            path = QFileDialog.getExistingDirectory(self, f"Chọn {label_text}", start_dir)
            if path:
                inp.setText(path)
        elif kind == "save":
            default = inp.text() or "final.mp4"
            path, _ = QFileDialog.getSaveFileName(self, f"Chọn {label_text}", default,
                                                  "MP4 (*.mp4)")
            if path:
                inp.setText(path)

    # -------------------------------------------------------- Card 2
    def _card_ghep_video(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        title = QLabel("⚙️ Tùy chọn ghép video")
        title.setStyleSheet(_title_style())
        v.addWidget(title)

        # Khung hình (aspect)
        row = QHBoxLayout()
        lbl = QLabel("Khung hình:")
        lbl.setStyleSheet(_label_style())
        self.rad_16_9 = QRadioButton("16:9 ngang (YouTube)")
        self.rad_9_16 = QRadioButton("9:16 dọc (Shorts/TikTok)")
        self.rad_16_9.setChecked(True)
        row.addWidget(lbl)
        row.addWidget(self.rad_16_9)
        row.addWidget(self.rad_9_16)
        row.addStretch()
        v.addLayout(row)

        # Image mode
        row = QHBoxLayout()
        lbl = QLabel("Cách rải ảnh:")
        lbl.setStyleSheet(_label_style())
        self.cmb_img_mode = QComboBox()
        for text, data in IMAGE_MODES:
            self.cmb_img_mode.addItem(text, data)
        row.addWidget(lbl)
        row.addWidget(self.cmb_img_mode)
        row.addStretch()
        v.addLayout(row)

        # Clip fit + Clip audio
        row = QHBoxLayout()
        lbl = QLabel("Clip fit:")
        lbl.setStyleSheet(_label_style())
        self.cmb_clip_fit = QComboBox()
        for text, data in CLIP_FITS:
            self.cmb_clip_fit.addItem(text, data)
        row.addWidget(lbl)
        row.addWidget(self.cmb_clip_fit)
        self.chk_keep_clip_audio = QCheckBox("🎧 Giữ tiếng gốc của clip")
        row.addWidget(self.chk_keep_clip_audio)
        row.addStretch()
        v.addLayout(row)

        # Transition + xfade duration
        row = QHBoxLayout()
        lbl = QLabel("Chuyển cảnh:")
        lbl.setStyleSheet(_label_style())
        self.cmb_transition = QComboBox()
        self.cmb_transition.addItems(TRANSITIONS)
        self.cmb_transition.setCurrentText("none")
        row.addWidget(lbl)
        row.addWidget(self.cmb_transition)
        lbl2 = QLabel("⏱ xfade (s):")
        lbl2.setStyleSheet(_label_style())
        self.spin_xfade = QDoubleSpinBox()
        self.spin_xfade.setRange(0.0, 3.0)
        self.spin_xfade.setSingleStep(0.05)
        self.spin_xfade.setValue(0.5)
        row.addWidget(lbl2)
        row.addWidget(self.spin_xfade)
        row.addStretch()
        v.addLayout(row)

        # Max scenes (preview) + seconds_per_image
        row = QHBoxLayout()
        lbl = QLabel("Preview N cảnh đầu:")
        lbl.setStyleSheet(_label_style())
        self.spin_max_scenes = QSpinBox()
        self.spin_max_scenes.setRange(0, 999)
        self.spin_max_scenes.setValue(0)
        self.spin_max_scenes.setSpecialValueText("(tắt — render tất cả)")
        row.addWidget(lbl)
        row.addWidget(self.spin_max_scenes)

        lbl2 = QLabel("🕒 Giây/ảnh (0=tự động):")
        lbl2.setStyleSheet(_label_style())
        self.spin_secs_per_img = QDoubleSpinBox()
        self.spin_secs_per_img.setRange(0.0, 60.0)
        self.spin_secs_per_img.setSingleStep(0.5)
        self.spin_secs_per_img.setValue(0.0)
        row.addWidget(lbl2)
        row.addWidget(self.spin_secs_per_img)
        row.addStretch()
        v.addLayout(row)

        # Hiệu ứng checkboxes (Ken Burns / sub / crossfade)
        row = QHBoxLayout()
        self.chk_kenburns = QCheckBox("🎬 Ken Burns (zoom ảnh tĩnh)")
        self.chk_kenburns.setChecked(True)
        self.chk_sub = QCheckBox("💬 Chèn phụ đề từ SRT")
        self.chk_sub.setChecked(True)
        row.addWidget(self.chk_kenburns)
        row.addWidget(self.chk_sub)
        row.addStretch()
        v.addLayout(row)
        return card

    # -------------------------------------------------------- Card 3: Sub
    def _card_phu_de(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        title = QLabel("💬 Phụ đề chuyên sâu")
        title.setStyleSheet(_title_style())
        v.addWidget(title)

        # Mode (word/line/kara)
        row = QHBoxLayout()
        lbl = QLabel("Cách hiện:")
        lbl.setStyleSheet(_label_style())
        self.cmb_sub_mode = QComboBox()
        for text, data in SUB_MODES:
            self.cmb_sub_mode.addItem(text, data)
        row.addWidget(lbl)
        row.addWidget(self.cmb_sub_mode)
        row.addStretch()
        v.addLayout(row)

        # Font family + size
        row = QHBoxLayout()
        lbl = QLabel("Phông chữ:")
        lbl.setStyleSheet(_label_style())
        self.cmb_font = QComboBox()
        self.cmb_font.addItems(["Arial Black", "Arial", "Impact", "Segoe UI Black",
                                "Tahoma", "Verdana", "Calibri"])
        row.addWidget(lbl)
        row.addWidget(self.cmb_font)
        lbl2 = QLabel("Cỡ chữ (px):")
        lbl2.setStyleSheet(_label_style())
        self.spin_fontsize = QSpinBox()
        self.spin_fontsize.setRange(20, 140)
        self.spin_fontsize.setValue(52)
        row.addWidget(lbl2)
        row.addWidget(self.spin_fontsize)
        row.addStretch()
        v.addLayout(row)

        # Cỡ nhanh (radio group)
        row = QHBoxLayout()
        lbl = QLabel("Cỡ nhanh:")
        lbl.setStyleSheet(_label_style())
        self.size_group = QButtonGroup(self)
        size_labels = [("Nhỏ", 36), ("Vừa", 52), ("To", 72), ("Khổng lồ", 96)]
        for txt, sz in size_labels:
            rb = QRadioButton(f"{txt} ({sz})")
            rb.toggled.connect(lambda checked, s=sz: self.spin_fontsize.setValue(s)
                                if checked else None)
            self.size_group.addButton(rb)
            row.addWidget(rb)
        row.addStretch()
        v.addLayout(row)

        # Màu chữ + Màu viền (ColorButton)
        row = QHBoxLayout()
        lbl = QLabel("Màu chữ:")
        lbl.setStyleSheet(_label_style())
        self.btn_sub_color = ColorButton(initial_hex="#FFFFFF", title="Chọn màu chữ sub")
        row.addWidget(lbl)
        row.addWidget(self.btn_sub_color)

        lbl2 = QLabel("Màu viền:")
        lbl2.setStyleSheet(_label_style())
        self.btn_sub_outline = ColorButton(initial_hex="#000000", title="Chọn màu viền sub")
        row.addWidget(lbl2)
        row.addWidget(self.btn_sub_outline)
        row.addStretch()
        v.addLayout(row)
        return card

    # -------------------------------------------------------- Card 4: Màu FX
    def _card_mau_fx(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        title = QLabel("🎨 Màu phim & Hiệu ứng")
        title.setStyleSheet(_title_style())
        v.addWidget(title)

        # Color preset
        row = QHBoxLayout()
        lbl = QLabel("Preset màu:")
        lbl.setStyleSheet(_label_style())
        self.cmb_color = QComboBox()
        for text, data in COLORS:
            self.cmb_color.addItem(text, data)
        row.addWidget(lbl)
        row.addWidget(self.cmb_color)
        row.addStretch()
        v.addLayout(row)

        # Vignette + Grain
        row = QHBoxLayout()
        self.chk_vignette = QCheckBox("🌑 Vignette (tối góc)")
        self.chk_grain = QCheckBox("🎞 Hạt phim (grain)")
        row.addWidget(self.chk_vignette)
        row.addWidget(self.chk_grain)
        row.addStretch()
        v.addLayout(row)

        # Title text + title_sec
        row = QHBoxLayout()
        lbl = QLabel("Tiêu đề mở đầu:")
        lbl.setStyleSheet(_label_style())
        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("(trống = không có)")
        row.addWidget(lbl)
        row.addWidget(self.inp_title)
        lbl2 = QLabel("⏱ (giây):")
        lbl2.setStyleSheet(_label_style())
        self.spin_title_sec = QDoubleSpinBox()
        self.spin_title_sec.setRange(1.0, 30.0)
        self.spin_title_sec.setSingleStep(0.5)
        self.spin_title_sec.setValue(4.0)
        row.addWidget(lbl2)
        row.addWidget(self.spin_title_sec)
        row.addStretch()
        v.addLayout(row)

        # FPS + encoder
        row = QHBoxLayout()
        lbl = QLabel("FPS (0 = tự chọn):")
        lbl.setStyleSheet(_label_style())
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(0, 120)
        self.spin_fps.setValue(0)
        lbl2 = QLabel("Encoder:")
        lbl2.setStyleSheet(_label_style())
        self.cmb_encoder = QComboBox()
        self.cmb_encoder.addItems(["auto", "cpu"])  # khớp CLI choices
        row.addWidget(lbl)
        row.addWidget(self.spin_fps)
        row.addWidget(lbl2)
        row.addWidget(self.cmb_encoder)
        row.addStretch()
        v.addLayout(row)
        return card

    # -------------------------------------------------------- Card 5: Audio
    def _card_am_thanh(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        title = QLabel("🎵 Âm thanh")
        title.setStyleSheet(_title_style())
        v.addWidget(title)

        # 3 volume spin
        row = QHBoxLayout()
        lbl = QLabel("🔊 Voice:")
        lbl.setStyleSheet(_label_style())
        self.spin_voice_vol = QDoubleSpinBox()
        self.spin_voice_vol.setRange(0.0, 2.0)
        self.spin_voice_vol.setSingleStep(0.05)
        self.spin_voice_vol.setValue(1.0)
        row.addWidget(lbl)
        row.addWidget(self.spin_voice_vol)

        lbl2 = QLabel("🎶 Nhạc nền:")
        lbl2.setStyleSheet(_label_style())
        self.spin_bgm_vol = QDoubleSpinBox()
        self.spin_bgm_vol.setRange(0.0, 2.0)
        self.spin_bgm_vol.setSingleStep(0.05)
        self.spin_bgm_vol.setValue(0.18)
        row.addWidget(lbl2)
        row.addWidget(self.spin_bgm_vol)

        lbl3 = QLabel("🎬 Tiếng clip:")
        lbl3.setStyleSheet(_label_style())
        self.spin_clip_vol = QDoubleSpinBox()
        self.spin_clip_vol.setRange(0.0, 2.0)
        self.spin_clip_vol.setSingleStep(0.05)
        self.spin_clip_vol.setValue(0.25)
        row.addWidget(lbl3)
        row.addWidget(self.spin_clip_vol)

        lbl4 = QLabel("💥 SFX:")
        lbl4.setStyleSheet(_label_style())
        self.spin_sfx_vol = QDoubleSpinBox()
        self.spin_sfx_vol.setRange(0.0, 2.0)
        self.spin_sfx_vol.setSingleStep(0.05)
        self.spin_sfx_vol.setValue(0.5)
        row.addWidget(lbl4)
        row.addWidget(self.spin_sfx_vol)
        row.addStretch()
        v.addLayout(row)

        # Ducking
        row = QHBoxLayout()
        self.chk_ducking = QCheckBox("🎚 Tự hạ nhạc khi có lời (Ducking)")
        self.chk_ducking.setChecked(True)
        row.addWidget(self.chk_ducking)
        row.addStretch()
        v.addLayout(row)
        return card

    # -------------------------------------------------------- Card 6: Branding
    def _card_branding(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        title = QLabel("🏷 Thương hiệu & Logo")
        title.setStyleSheet(_title_style())
        v.addWidget(title)

        row = QHBoxLayout()
        lbl = QLabel("Vị trí logo:")
        lbl.setStyleSheet(_label_style())
        self.cmb_logo_pos = QComboBox()
        for text, data in LOGO_POS:
            self.cmb_logo_pos.addItem(text, data)
        self.cmb_logo_pos.setCurrentIndex(3)  # default br
        row.addWidget(lbl)
        row.addWidget(self.cmb_logo_pos)

        lbl2 = QLabel("Kiểu logo:")
        lbl2.setStyleSheet(_label_style())
        self.cmb_logo_shape = QComboBox()
        for text, data in LOGO_SHAPES:
            self.cmb_logo_shape.addItem(text, data)
        row.addWidget(lbl2)
        row.addWidget(self.cmb_logo_shape)
        row.addStretch()
        v.addLayout(row)

        row = QHBoxLayout()
        lbl = QLabel("Cỡ logo (px):")
        lbl.setStyleSheet(_label_style())
        self.spin_logo_size = QSpinBox()
        self.spin_logo_size.setRange(24, 512)
        self.spin_logo_size.setValue(96)
        row.addWidget(lbl)
        row.addWidget(self.spin_logo_size)

        lbl2 = QLabel("Độ mờ:")
        lbl2.setStyleSheet(_label_style())
        self.spin_logo_opacity = QDoubleSpinBox()
        self.spin_logo_opacity.setRange(0.0, 1.0)
        self.spin_logo_opacity.setSingleStep(0.05)
        self.spin_logo_opacity.setValue(0.85)
        row.addWidget(lbl2)
        row.addWidget(self.spin_logo_opacity)
        row.addStretch()
        v.addLayout(row)
        return card

    # ---------------------------------------------------------------- WIRE
    def _collect_cfg(self) -> dict:
        """Thu thập TOÀN BỘ settings từ widget -> dict cfg.

        Số key khớp với `services.render_service._build_args._defaults`.
        """
        p = self.path_inputs
        return {
            # Path/IO
            "input_dir":     os.path.dirname(p["File PHỤ ĐỀ (SRT):"].text()) or "input",
            "voice":         p["File VOICEOVER:"].text().strip() or None,
            "scenes":        p["📋 File bảng cảnh (CSV):"].text().strip() or None,
            "intro":         p["🎬 Video intro (tuỳ chọn):"].text().strip() or None,
            "outro":         p["🏁 Video outro (tuỳ chọn):"].text().strip() or None,
            "bgm":           p["🎵 Nhạc nền - BGM:"].text().strip() or None,
            "sfx":           p["💥 SFX chuyển cảnh:"].text().strip() or None,
            "logo":          p["💧 Logo/Watermark:"].text().strip() or None,
            # Aspect / image / clip
            "aspect":        "16:9" if self.rad_16_9.isChecked() else "9:16",
            "image_mode":    self.cmb_img_mode.currentData(),
            "clip_fit":      self.cmb_clip_fit.currentData(),
            "transition":    self.cmb_transition.currentText(),
            "xfade_duration": self.spin_xfade.value(),
            "max_scenes":    self.spin_max_scenes.value() or None,
            "seconds_per_image": self.spin_secs_per_img.value() or None,
            # Toggles
            "no_kenburns":   not self.chk_kenburns.isChecked(),
            "no_subtitles":  not self.chk_sub.isChecked(),
            "vignette":      self.chk_vignette.isChecked(),
            "grain":         self.chk_grain.isChecked(),
            "keep_clip_audio": self.chk_keep_clip_audio.isChecked(),
            "no_duck":       not self.chk_ducking.isChecked(),
            "keep_temp":     False,
            # Subtitle style
            "sub_mode":       self.cmb_sub_mode.currentData(),
            "sub_font":       self.cmb_font.currentText(),
            "sub_size":       self.spin_fontsize.value(),
            "karaoke_color":  self.btn_sub_color.hex_value,
            "sub_outline_color": self.btn_sub_outline.hex_value,
            # Visual FX
            "color":          self.cmb_color.currentData(),
            "title_text":     self.inp_title.text().strip() or None,
            "title_sec":      self.spin_title_sec.value(),
            "fps":            self.spin_fps.value() or None,
            "encoder":        self.cmb_encoder.currentText(),
            # Audio
            "voice_volume":   self.spin_voice_vol.value(),
            "bgm_volume":     self.spin_bgm_vol.value(),
            "clip_volume":    self.spin_clip_vol.value(),
            "sfx_volume":     self.spin_sfx_vol.value(),
            # Branding
            "logo_pos":       self.cmb_logo_pos.currentData(),
            "logo_shape":     self.cmb_logo_shape.currentData(),
            "logo_size":      self.spin_logo_size.value(),
            "logo_opacity":   self.spin_logo_opacity.value(),
        }

    # ---------------------------------------------------------------- Actions
    def run_render(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang chuẩn bị dữ liệu để Render...", "#D4D4D4")

        p = self.path_inputs
        data = {
            "cfg":     self._collect_cfg(),
            "srt":     p["File PHỤ ĐỀ (SRT):"].text().strip(),
            "img_dir": p["Thư mục ẢNH/CLIP:"].text().strip(),
            "output":  p["Xuất ra MP4:"].text().strip(),
            "channel": self.cmb_channel.currentText(),
        }
        if not data["srt"]:
            QMessageBox.warning(self, "Thiếu", "Chưa chọn file SRT.")
            return
        if not data["img_dir"]:
            QMessageBox.warning(self, "Thiếu", "Chưa chọn thư mục ẢNH/CLIP.")
            return
        if not data["output"]:
            QMessageBox.warning(self, "Thiếu", "Chưa chọn file MP4 đầu ra.")
            return

        self.btn_render.setEnabled(False)
        self.btn_render.setText("⏳ ĐANG RENDER...")
        self.worker = RenderWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.finished_signal.connect(self.on_render_finished)
        self.worker.start()

    def run_preview(self):
        """Preview = render với max_scenes=1 (chạy nhanh thử 1 cảnh)."""
        p = self.path_inputs
        if not p["File PHỤ ĐỀ (SRT):"].text().strip():
            QMessageBox.warning(self, "Thiếu", "Chưa chọn file SRT.")
            return
        cfg = self._collect_cfg()
        cfg["max_scenes"] = 1  # tự động preview 1 cảnh

        data = {
            "cfg":     cfg,
            "srt":     p["File PHỤ ĐỀ (SRT):"].text().strip(),
            "img_dir": p["Thư mục ẢNH/CLIP:"].text().strip(),
            "output":  (p["Xuất ra MP4:"].text().strip() or "preview.mp4").replace(".mp4", "_preview.mp4"),
            "channel": self.cmb_channel.currentText(),
        }
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("👁 Preview 1 cảnh đầu tiên...", "#0066FF")
        self.btn_preview.setEnabled(False)
        self.worker = RenderWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
        self.worker.finished_signal.connect(self.on_preview_finished)
        self.worker.start()

    def on_preview_finished(self, success, msg):
        self.btn_preview.setEnabled(True)
        if success:
            QMessageBox.information(self, "Preview OK", "Đã render preview 1 cảnh!")

    def run_queue_add(self):
        """Thêm job vào hàng đợi (gọi main_window thêm nếu có API)."""
        main_win = self.window()
        if hasattr(main_win, "add_queue_job"):
            data = {
                "cfg":     self._collect_cfg(),
                "srt":     self.path_inputs["File PHỤ ĐỀ (SRT):"].text().strip(),
                "img_dir": self.path_inputs["Thư mục ẢNH/CLIP:"].text().strip(),
                "output":  self.path_inputs["Xuất ra MP4:"].text().strip(),
            }
            main_win.add_queue_job(data)
            if hasattr(main_win, "append_log"):
                main_win.append_log(f"➕ Đã thêm vào hàng đợi: {data['output']}", "#28A745")
        else:
            QMessageBox.information(
                self, "Hàng đợi",
                "Hàng đợi chưa wire (Phase 5 Mở rộng). Vui lòng qua tab Hàng đợi để thêm job.",
            )

    # ---------------------------------------------------------------- Old on_finished (keep API)
    def on_render_finished(self, success, msg):
        self.btn_render.setEnabled(True)
        self.btn_render.setText("▶ RENDER VIDEO")
        if success:
            QMessageBox.information(self, "Thành công", "Render Video hoàn tất!")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra:\n{msg}")