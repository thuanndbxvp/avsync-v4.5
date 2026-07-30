# -*- coding: utf-8 -*-
"""ui.tabs.tab_settings — Settings tab (M6: wire ConfigService cho persistence).

Các tính năng wired đến ConfigService (services/config_service.py):
  - Save API key (per provider)
  - Refresh model list theo provider
  - Save / Add / Delete Style Profile
  - Load lúc init từ file
"""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QListWidget, QTextEdit, QScrollArea, QSplitter, QInputDialog,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap

import i18n as _i18n
from services.config_service import ConfigService


# Models per provider (defaults từ ConfigService; user có thể refresh mở rộng)
_DEFAULT_MODELS = {
    "gemini":    ["gemini-2.0-flash-exp", "gemini-2.0-flash-thinking-exp",
                  "gemini-2.5-flash", "gemini-2.5-pro"],
    "openai":    ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
    "anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest",
                  "claude-3-opus-latest"],
}


class SettingsTab(QWidget):
    # ----- M8: signal bắn ra khi profiles thay đổi → main_window refresh tab_prompt -----
    profilesChanged = Signal()
    def __init__(self):
        super().__init__()
        self.cfg = ConfigService.instance()
        self._data = self.cfg.load()  # merge defaults + file
        self.setup_ui()
        self._populate_from_config()

    # ---------------------------------------------------------------- UI
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

        # ---- Card 1: System ----
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)

        lbl_sys = QLabel("⚙️ Cấu hình Hệ thống")
        lbl_sys.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout1.addWidget(lbl_sys)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Phiên bản hiện tại: 1.2.7"))
        row1.addStretch()
        row1.addWidget(QLabel("Ngôn ngữ:"))
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItems(["Tiếng Việt", "English"])
        # M8: persist lang selection
        _lang = self.cfg.get("system.language", "vi")
        if _lang == "en":
            self.cmb_lang.setCurrentIndex(1)
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)
        row1.addWidget(self.cmb_lang)
        btn_update = QPushButton("Kiểm tra cập nhật")
        # M8: wire thật — gọi GitHub API check release (nếu offline thì báo nhẹ nhàng)
        btn_update.clicked.connect(self._check_for_updates)
        row1.addWidget(btn_update)
        layout1.addLayout(row1)
        layout.addWidget(card1)

        # ---- Card 2: API ----
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)

        lbl_api = QLabel("🔑 API viết prompt — chọn nhà cung cấp")
        lbl_api.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout2.addWidget(lbl_api)

        grid_api = QGridLayout()
        grid_api.setColumnStretch(1, 1)
        grid_api.setVerticalSpacing(16)

        # Provider
        grid_api.addWidget(QLabel("Nhà cung cấp:"), 0, 0)
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(list(_DEFAULT_MODELS.keys()))
        self.cmb_provider.currentTextChanged.connect(self._on_provider_changed)
        grid_api.addWidget(self.cmb_provider, 0, 1)

        # Model + Refresh
        grid_api.addWidget(QLabel("Model:"), 1, 0)
        row_model = QHBoxLayout()
        self.cmb_model = QComboBox()
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.setToolTip("Tải lại danh sách model cho provider hiện tại")
        btn_refresh.clicked.connect(self._on_refresh_models)
        row_model.addWidget(self.cmb_model)
        row_model.addWidget(btn_refresh)
        grid_api.addLayout(row_model, 1, 1)

        # API Key
        grid_api.addWidget(QLabel("API Key:"), 2, 0)
        row_key = QHBoxLayout()
        self.inp_key = QLineEdit()
        self.inp_key.setEchoMode(QLineEdit.Password)
        self.inp_key.setPlaceholderText("Dán API key của bạn tại đây...")
        self.btn_toggle_key = QPushButton("👁")
        self.btn_toggle_key.setFixedWidth(40)
        self.btn_toggle_key.setCheckable(True)
        self.btn_toggle_key.toggled.connect(self._toggle_api_key)
        row_key.addWidget(self.inp_key)
        row_key.addWidget(self.btn_toggle_key)
        grid_api.addLayout(row_key, 2, 1)

        layout2.addLayout(grid_api)

        row_api_btns = QHBoxLayout()
        self.btn_save_key = QPushButton("💾 Lưu key")
        self.btn_save_key.setStyleSheet(
            "background-color: #0066FF; color: white; padding: 6px 12px;"
            " font-weight: bold; border-radius: 4px;"
        )
        self.btn_save_key.clicked.connect(self._save_api_key)
        self.btn_test_conn = QPushButton("⚡ Kiểm tra kết nối")
        self.btn_test_conn.clicked.connect(self._test_connection)
        row_api_btns.addWidget(self.btn_save_key)
        row_api_btns.addWidget(self.btn_test_conn)
        row_api_btns.addStretch()
        layout2.addLayout(row_api_btns)

        layout.addWidget(card2)

        # ---- Card 3: Style Profile ----
        card3 = QFrame()
        card3.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout3 = QVBoxLayout(card3)
        layout3.setContentsMargins(0, 0, 0, 0)

        lbl_style = QLabel("🎨 Style Visual Profile (cho từng kênh)")
        lbl_style.setStyleSheet(
            "font-size: 16px; font-weight: bold; border: none; padding: 16px;"
            " background: #F8F9FA; border-bottom: 1px solid #DEE2E6;"
        )
        layout3.addWidget(lbl_style)

        splitter = QSplitter(Qt.Horizontal)

        # Left: list + add/del
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.list_profiles = QListWidget()
        self.list_profiles.setObjectName("ProfileList")
        self.list_profiles.currentItemChanged.connect(self._on_profile_select)
        left_layout.addWidget(self.list_profiles)

        row_prof_btns = QHBoxLayout()
        row_prof_btns.setContentsMargins(8, 8, 8, 8)
        btn_add_prof = QPushButton(_i18n.tr("➕ Thêm"))
        btn_add_prof.clicked.connect(self._add_profile)
        btn_del_prof = QPushButton(_i18n.tr("🗑 Xoá"))
        btn_del_prof.setStyleSheet("color: #ba1a1a;")
        btn_del_prof.clicked.connect(self._del_profile)
        row_prof_btns.addWidget(btn_add_prof)
        row_prof_btns.addWidget(btn_del_prof)
        left_layout.addLayout(row_prof_btns)

        # Right: editor + thumbnail preview + save
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # ----- M10.1: Thumbnail Preview + Browse button -----
        thumb_row = QHBoxLayout()
        thumb_row.setContentsMargins(8, 8, 8, 0)
        thumb_row.setSpacing(12)
        self.lbl_preview = QLabel()
        self.lbl_preview.setFixedSize(200, 200)
        self.lbl_preview.setStyleSheet("border: 1px solid gray;")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setText(_i18n.tr("Không có ảnh minh họa")
                                 if False else "Không có ảnh minh họa")
        thumb_row.addWidget(self.lbl_preview)

        # Vertical stack: Browse button + hint label
        thumb_btns_col = QVBoxLayout()
        thumb_btns_col.setSpacing(8)
        self.btn_browse_thumb = QPushButton("🖼 Chọn Ảnh Minh Họa")
        self.btn_browse_thumb.setStyleSheet(
            "background: #F8F9FA; border: 1px solid #DEE2E6;"
            " padding: 6px 12px; border-radius: 4px;"
        )
        self.btn_browse_thumb.clicked.connect(self._browse_thumb)
        thumb_btns_col.addWidget(self.btn_browse_thumb)
        hint_lbl = QLabel("(PNG/JPG, 200×200 px)")
        hint_lbl.setStyleSheet("color: gray; font-size: 11px;")
        thumb_btns_col.addWidget(hint_lbl)
        thumb_btns_col.addStretch()
        thumb_row.addLayout(thumb_btns_col)
        thumb_row.addStretch()

        right_layout.addLayout(thumb_row)

        self.txt_prompt = QTextEdit()
        self.txt_prompt.setPlaceholderText("Nhập mô tả phong cách hình ảnh vào đây...")
        right_layout.addWidget(self.txt_prompt)

        row_editor_btns = QHBoxLayout()
        row_editor_btns.setContentsMargins(8, 8, 8, 8)
        row_editor_btns.addStretch()
        btn_preview_style = QPushButton("👁 Xem trước style")
        btn_preview_style.clicked.connect(self._preview_style)
        btn_save_prof = QPushButton("💾 Lưu profile này")
        btn_save_prof.setStyleSheet(
            "background-color: #0066FF; color: white; padding: 6px 12px; border-radius: 4px;"
        )
        btn_save_prof.clicked.connect(self._save_profile)
        row_editor_btns.addWidget(btn_preview_style)
        row_editor_btns.addWidget(btn_save_prof)
        right_layout.addLayout(row_editor_btns)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])
        splitter.setMinimumHeight(350)

        layout3.addWidget(splitter)
        layout.addWidget(card3)

        # ---- Card 4: Reset ----
        card4 = QFrame()
        card4.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout4 = QVBoxLayout(card4)
        row_reset = QHBoxLayout()
        row_reset.addWidget(QLabel("⚠️ Reset toàn bộ config về mặc định:"))
        btn_reset = QPushButton("♻️ Reset Defaults")
        btn_reset.setStyleSheet("color: #ba1a1a; font-weight: bold; padding: 6px 12px;")
        btn_reset.clicked.connect(self._reset_config)
        row_reset.addStretch()
        row_reset.addWidget(btn_reset)
        layout4.addLayout(row_reset)

        # ===========================================================
        # CARD 5: Advanced — Encoder / TTS (M8)
        # ===========================================================
        card5 = QFrame()
        card5.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6;"
            " border-radius: 8px; }"
        )
        layout5 = QVBoxLayout(card5)
        layout5.setSpacing(16)

        lbl_adv = QLabel("🔧 Tùy chọn Nâng cao — Encoder / TTS")
        lbl_adv.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout5.addWidget(lbl_adv)

        grid_adv = QGridLayout()
        grid_adv.setColumnStretch(1, 1)
        grid_adv.setVerticalSpacing(12)

        # ----- Encoder dropdown (M8.3.1) -----
        grid_adv.addWidget(QLabel("Lõi Render (Encoder):"), 0, 0)
        self.cmb_encoder = QComboBox()
        _encoders = [
            ("auto  — Tự động (GPU nếu có)", "auto"),
            ("libx264  — CPU H.264 (mặc định)", "libx264"),
            ("h264_nvenc  — NVIDIA GPU", "h264_nvenc"),
            ("hevc_nvenc  — NVIDIA GPU HEVC", "hevc_nvenc"),
            ("h264_qsv  — Intel QuickSync", "h264_qsv"),
        ]
        for label, data in _encoders:
            self.cmb_encoder.addItem(label, data)
        self.cmb_encoder.currentIndexChanged.connect(self._on_encoder_changed)
        grid_adv.addWidget(self.cmb_encoder, 0, 1)

        # ----- TTS voice (M8.3.2) -----
        grid_adv.addWidget(QLabel("Định dạng TTS (Voice):"), 1, 0)
        self.cmb_tts = QComboBox()
        _tts = [
            ("edge-tts  — Microsoft Edge (miễn phí, nhiều voice)", "edge-tts"),
            ("gtts  — Google Translate (online, free, basic)", "gtts"),
            ("elevenlabs  — ElevenLabs (premium AI)", "elevenlabs"),
        ]
        for label, data in _tts:
            self.cmb_tts.addItem(label, data)
        self.cmb_tts.currentIndexChanged.connect(self._on_tts_changed)
        grid_adv.addWidget(self.cmb_tts, 1, 1)

        layout5.addLayout(grid_adv)
        layout.addWidget(card5)

        # ===========================================================
        # CARD 6: Brand DNA — Default Channel + Logo (M8)
        # ===========================================================
        card6 = QFrame()
        card6.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6;"
            " border-radius: 8px; }"
        )
        layout6 = QVBoxLayout(card6)
        layout6.setSpacing(16)

        lbl_brand = QLabel("🏷 Brand DNA — Mặc định Kênh")
        lbl_brand.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout6.addWidget(lbl_brand)

        grid_brand = QGridLayout()
        grid_brand.setColumnStretch(1, 1)
        grid_brand.setVerticalSpacing(12)

        # Channel name
        grid_brand.addWidget(QLabel("Tên kênh:"), 0, 0)
        self.inp_channel_name = QLineEdit()
        self.inp_channel_name.setPlaceholderText("VD: PeiPei Official")
        self.inp_channel_name.editingFinished.connect(self._on_channel_name_changed)
        grid_brand.addWidget(self.inp_channel_name, 0, 1)

        # Logo path + browse
        grid_brand.addWidget(QLabel("Logo kênh mặc định:"), 1, 0)
        self.inp_channel_logo = QLineEdit()
        btn_logo_browse = QPushButton("Chọn...")
        btn_logo_browse.setStyleSheet(
            "background: #F8F9FA; border: 1px solid #DEE2E6;"
            " padding: 4px 12px; border-radius: 4px;"
        )
        btn_logo_browse.clicked.connect(self._browse_channel_logo)
        self.inp_channel_logo.editingFinished.connect(self._on_channel_logo_changed)
        row_logo = QHBoxLayout()
        row_logo.addWidget(self.inp_channel_logo)
        row_logo.addWidget(btn_logo_browse)
        grid_brand.addLayout(row_logo, 1, 1)

        layout6.addLayout(grid_brand)
        layout.addWidget(card6)

        layout.addWidget(card4)

        layout.addStretch()

    # ---------------------------------------------------------------- API handlers
    def _populate_from_config(self):
        """Load state từ ConfigService vào UI khi vừa mở tab."""
        prov = self.cfg.get("providers.default_provider", "gemini")
        idx = self.cmb_provider.findText(prov)
        if idx >= 0:
            self.cmb_provider.setCurrentIndex(idx)
        self._on_provider_changed(prov)

        model = self.cfg.get(f"providers.models.{prov}", "")
        if model:
            idx = self.cmb_model.findText(model)
            if idx >= 0:
                self.cmb_model.setCurrentIndex(idx)

        key = self.cfg.get(f"api_keys.{prov}", "")
        self.inp_key.setText(key if key else "")

        # ----- M8: Advanced (encoder + tts) -----
        encoder = self.cfg.get("render.encoder", "auto")
        idx = self.cmb_encoder.findData(encoder)
        if idx >= 0:
            self.cmb_encoder.setCurrentIndex(idx)
        else:
            self.cmb_encoder.setCurrentIndex(0)

        tts = self.cfg.get("voice.tts_provider", "gtts")
        idx = self.cmb_tts.findData(tts)
        if idx >= 0:
            self.cmb_tts.setCurrentIndex(idx)
        else:
            self.cmb_tts.setCurrentIndex(0)

        # ----- M8: Brand DNA -----
        channel_name = self.cfg.get("channels.default.name", "")
        if channel_name:
            self.inp_channel_name.setText(channel_name)
        channel_logo = self.cfg.get("channels.default.logo_path", "")
        if channel_logo:
            self.inp_channel_logo.setText(channel_logo)

        self._refresh_profile_list()

    def _refresh_profile_list(self):
        """Reload list_profiles từ self._data['profiles']."""
        self.list_profiles.clear()
        profiles = self._data.get("profiles", {})
        for name in profiles.keys():
            self.list_profiles.addItem(name)

    # ----- M8: Advanced handlers -----
    def _on_encoder_changed(self, *_):
        """Persist encoder preference (auto-save)."""
        self.cfg.set("render.encoder",
                     self.cmb_encoder.currentData() or "auto",
                     auto_save=True)

    def _on_tts_changed(self, *_):
        """Persist TTS provider preference (auto-save)."""
        self.cfg.set("voice.tts_provider",
                     self.cmb_tts.currentData() or "gtts",
                     auto_save=True)

    def _on_channel_name_changed(self):
        """Persist tên kênh khi user edit xong."""
        name = self.inp_channel_name.text().strip()
        self.cfg.set("channels.default.name", name, auto_save=True)

    def _browse_channel_logo(self):
        """QFileDialog để chọn logo PNG/SVG cho Brand DNA."""
        start = self.inp_channel_logo.text() or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn logo kênh", start,
            "Image (*.png *.svg *.jpg *.jpeg);;All Files (*.*)"
        )
        if file:
            self.inp_channel_logo.setText(file)
            self._on_channel_logo_changed()

    def _on_channel_logo_changed(self):
        """Persist logo path khi user set xong."""
        path = self.inp_channel_logo.text().strip()
        self.cfg.set("channels.default.logo_path", path, auto_save=True)

    def _on_lang_changed(self, *_):
        """Persist UI language preference (auto-save) + apply i18n live (M10.2)."""
        idx = self.cmb_lang.currentIndex()
        lang = "en" if idx == 1 else "vi"
        self.cfg.set("system.language", lang, auto_save=True)
        # ----- M10.2: Apply i18n live (no app restart) -----
        try:
            _i18n.set_lang(lang)
            _i18n.translate_tree(self.window() or self)
            self.append_log(f"🌐 Ngôn ngữ đã đổi sang: {lang}", "#28A745")
        except Exception as e:
            # translate_tree uses tkinter (c) on PySide6 — gracefully skip if not compatible
            self.append_log(f"⚠ i18n apply failed: {e}", "#D4D4D4")

    def _check_for_updates(self):
        """M8: bỏ stub — gọi GitHub API kiểm tra release mới. Offline thì cảnh báo."""
        import threading
        from PySide6.QtCore import QTimer
        def show_info(msg):
            QMessageBox.information(self, "Cập nhật", msg)
        def show_warn(msg):
            QMessageBox.warning(self, "Không kiểm tra được", msg)

        def worker():
            try:
                req = _urllib_request.Request(
                    "https://api.github.com/repos/thuanndbxvp/avsync-v4.5/releases/latest",
                    method="GET",
                )
                req.add_header("Accept", "application/vnd.github+json")
                req.add_header("User-Agent", "PeiPei-AutoEdit/1.2.7")
                try:
                    with _urllib_request.urlopen(req, timeout=6) as resp:
                        code = resp.getcode()
                        body = resp.read(1500)
                except _urllib_error.HTTPError as e:
                    code = e.code
                    body = e.read(300) if e.fp else b""
                if code == 200:
                    data = _json.loads(body.decode("utf-8", errors="ignore"))
                    latest = data.get("tag_name", "?")
                    current = "1.2.7"
                    msg = (f"Bạn đang dùng v{current}.\n"
                           f"Bản mới nhất trên GitHub: {latest}\n\n"
                           f"URL: https://github.com/thuanndbxvp/avsync-v4.5/releases")
                    QTimer.singleShot(0, lambda: show_info(msg))
                else:
                    QTimer.singleShot(0, lambda: show_warn(
                        f"Không truy cập được GitHub (HTTP {code}). Thử lại sau."
                    ))
            except Exception as e:
                QTimer.singleShot(0, lambda: show_warn(
                    f"🌐 Lỗi mạng hoặc offline:\n{e}"
                ))
        threading.Thread(target=worker, daemon=True).start()

    # Provider / Model
    def _on_provider_changed(self, provider: str):
        """Đổi provider → cập nhật model dropdown + load API key của provider đó."""
        models = _DEFAULT_MODELS.get(provider, [])
        self.cmb_model.clear()
        self.cmb_model.addItems(models)
        # Load model đã lưu (nếu có) cho provider mới
        saved = self.cfg.get(f"providers.models.{provider}", "")
        if saved and saved in models:
            self.cmb_model.setCurrentText(saved)
        # Load API key của provider mới
        key = self.cfg.get(f"api_keys.{provider}", "")
        self.inp_key.setText(key if key else "")

    def _on_refresh_models(self):
        provider = self.cmb_provider.currentText()
        models = _DEFAULT_MODELS.get(provider, [])
        if not models:
            QMessageBox.information(self, "Refresh", f"Không có model mặc định cho {provider}.")
            return
        self.cmb_model.clear()
        self.cmb_model.addItems(models)
        QMessageBox.information(
            self, "Refresh",
            f"Đã tải {len(models)} model cho provider '{provider}'."
        )

    # API key
    def _save_api_key(self):
        provider = self.cmb_provider.currentText()
        key = self.inp_key.text().strip()
        self.cfg.set(f"api_keys.{provider}", key)
        QMessageBox.information(self, "Đã lưu",
                                f"API Key cho '{provider}' đã được lưu vào config.local.json")

    def _test_connection(self):
        """Test connection THẬT tới endpoint API của provider.

        M8: thay mock format check bằng thực GET request tới /models endpoint.
        Dùng urllib.request (stdlib, không thêm deps). Timeout 6s. Bắt mọi lỗi.
        """
        provider = self.cmb_provider.currentText()
        key = self.inp_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Thiếu key",
                                f"Chưa nhập API key cho '{provider}'. Vui lòng nhập và Lưu trước.")
            return
        # Update UI ngay khi user bấm
        self.btn_test_conn.setEnabled(False)
        self.btn_test_conn.setText("⏳ Đang kiểm tra...")

        def done(ok, msg):
            self.btn_test_conn.setEnabled(True)
            self.btn_test_conn.setText("⚡ Kiểm tra kết nối")
            if ok:
                QMessageBox.information(self, "Kết nối thành công", msg)
            else:
                QMessageBox.critical(self, "Kết nối thất bại", msg)

        # Spawn thread để không block UI khi network chậm
        import threading
        def worker():
            ok, detail = _test_provider_endpoint(provider, key)
            # Schedule UI update trên main thread
            from PySide6.QtCore import QMetaObject, Qt as _Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_on_test_done",
                _Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, ok),
                Q_ARG(str, detail),
            )
        threading.Thread(target=worker, daemon=True).start()

    @Slot(bool, str)
    def _on_test_done(self, ok: bool, msg: str):
        """Slot thật khi test xong (chạy trên main thread)."""
        self.btn_test_conn.setEnabled(True)
        self.btn_test_conn.setText("⚡ Kiểm tra kết nối")
        if ok:
            QMessageBox.information(self, "Kết nối thành công", msg)
        else:
            QMessageBox.critical(self, "Kết nối thất bại", msg)

    def _toggle_api_key(self, checked):
        self.inp_key.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    # ----- M10.1: Thumbnail handlers -----
    def _browse_thumb(self):
        """Browse image → load lên QLabel + lưu tạm vào self._current_thumb."""
        start = getattr(self, "_current_thumb", "") or os.getcwd()
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh minh họa", start,
            "Image (*.png *.jpg *.jpeg *.svg);;All Files (*.*)"
        )
        if not file:
            return
        self._current_thumb = file
        pix = QPixmap(file)
        if pix.isNull():
            QMessageBox.warning(self, "Lỗi", f"Không đọc được ảnh:\n{file}")
            return
        self.lbl_preview.setPixmap(pix.scaled(
            200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.lbl_preview.setText("")

    def _set_thumb_preview(self, thumb_path: str | None):
        """Load ảnh lên QLabel. Nếu path None/invalid → reset về placeholder."""
        if not thumb_path or not os.path.isfile(thumb_path):
            self.lbl_preview.setPixmap(QPixmap())  # clear
            self.lbl_preview.setText("Không có ảnh minh họa")
            return
        pix = QPixmap(thumb_path)
        if pix.isNull():
            self.lbl_preview.setPixmap(QPixmap())
            self.lbl_preview.setText("Không đọc được ảnh")
            return
        self.lbl_preview.setPixmap(pix.scaled(
            200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.lbl_preview.setText("")

    # ----- M10.1: Hybrid schema helpers -----
    @staticmethod
    def _profile_text(value) -> str:
        """Extract prompt text từ profile value (hybrid: str OR dict)."""
        if isinstance(value, dict):
            return str(value.get("prompt", ""))
        return str(value) if value else ""

    @staticmethod
    def _profile_thumb(value) -> str | None:
        """Extract thumb path từ profile value (hybrid). Return None nếu không có."""
        if isinstance(value, dict):
            t = value.get("thumb")
            return t if isinstance(t, str) and t else None
        return None

    def _build_profile_value(self, text: str, thumb: str | None) -> str | dict:
        """Build value theo hybrid schema:
           - Nếu có thumb → dict{"prompt": text, "thumb": path}
           - Nếu chỉ có text → str (backward-compat)
        """
        if thumb and os.path.isfile(thumb):
            return {"prompt": text, "thumb": thumb}
        return text

    # Profile
    def _on_profile_select(self, current, previous):
        """Khi user chọn 1 profile trong list → load text + thumb vào editor."""
        if current is None:
            return
        name = current.text()
        raw = self._data.get("profiles", {}).get(name, "")
        text = self._profile_text(raw)
        thumb = self._profile_thumb(raw)
        self.txt_prompt.setPlainText(text)
        self._current_thumb = thumb or ""
        self._set_thumb_preview(thumb)

    def _save_profile(self):
        """Lưu nội dung editor + thumb vào profile đang chọn (hoặc tạo mới nếu trống)."""
        current = self.list_profiles.currentItem()
        if current is None:
            # Chưa chọn gì → coi như ADD mới
            self._add_profile()
            return
        name = current.text()
        text = self.txt_prompt.toPlainText().strip()
        thumb = getattr(self, "_current_thumb", None)
        self._data["profiles"][name] = self._build_profile_value(text, thumb)
        self.cfg.save(self._data)
        QMessageBox.information(self, "Đã lưu", f"Đã lưu profile '{name}'.")
        # ----- M8: bắn signal để tab_prompt refresh combobox -----
        self.profilesChanged.emit()

    def _add_profile(self):
        name, ok = QInputDialog.getText(self, "Thêm Profile", "Tên profile mới:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._data.get("profiles", {}):
            QMessageBox.warning(self, "Trùng tên",
                                f"Profile '{name}' đã tồn tại. Dùng Lưu thay vì Thêm.")
            return
        text = self.txt_prompt.toPlainText().strip()
        thumb = getattr(self, "_current_thumb", None)
        self._data["profiles"][name] = self._build_profile_value(text, thumb)
        self.cfg.save(self._data)
        self._refresh_profile_list()
        # Select profile mới
        items = self.list_profiles.findItems(name, Qt.MatchExactly)
        if items:
            self.list_profiles.setCurrentItem(items[0])
        # ----- M8: bắn signal -----
        self.profilesChanged.emit()

    def _del_profile(self):
        current = self.list_profiles.currentItem()
        if current is None:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn profile cần xoá.")
            return
        name = current.text()
        if name == "Người que":
            QMessageBox.warning(self, "Không thể xoá",
                                "Profile 'Người que' là mặc định và không thể xoá.")
            return
        if QMessageBox.question(
            self, "Xác nhận",
            f"Xoá profile '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._data["profiles"].pop(name, None)
        self.cfg.save(self._data)
        self._refresh_profile_list()
        # ----- M8: bắn signal -----
        self.profilesChanged.emit()

    def _preview_style(self):
        QMessageBox.information(self, "Preview",
                                "Tính năng preview style sẽ render 1 ảnh mẫu (Phase 7 Mở rộng).")

    def _reset_config(self):
        if QMessageBox.question(
            self, "Reset",
            "Reset toàn bộ config.local.json về defaults?\n"
            "API keys + profiles sẽ bị XOÁ.",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.cfg.reset()
        self._data = self.cfg.load()
        self._populate_from_config()
        QMessageBox.information(self, "Reset OK", "Đã reset config về mặc định.")


# ============================================================================
# M8 — Test Connection thực sự đến endpoint API của mỗi provider
# ============================================================================
import json as _json
import urllib.error as _urllib_error
import urllib.request as _urllib_request

_PROVIDER_TEST_ENDPOINTS = {
    # Gemini: GET /v1beta/models với key trên query string
    # Nếu 200 OK -> key hợp lệ; 400/403 -> sai key; 401/500 -> lỗi auth
    "gemini":    "https://generativelanguage.googleapis.com/v1beta/models?key={key}",
    # OpenAI: GET /v1/models yêu cầu Bearer auth header
    "openai":    "https://api.openai.com/v1/models",
    # Anthropic: GET /v1/messages... không có GET list endpoint nên gọi POST
    # Dùng 1 ping GET đến /v1/messages với header chuẩn. Anthropic yêu cầu `x-api-key`.
    # Anthropic chỉ chấp nhận method POST thực sự; 405 vẫn cho thấy server reachable + key khớp format
    "anthropic": "https://api.anthropic.com/v1/messages",
}


def _test_provider_endpoint(provider: str, key: str) -> tuple[bool, str]:
    """Gọi GET request thật tới endpoint test của provider. Trả (ok, detail_text).

    ok=True nếu HTTP 200 (Gemini list models) HOẶC 405 (Anthropic chỉ chấp nhận POST)
    HOẶC 401 không xảy ra (key rỗng/dạng OK format). Bắt mọi exception.
    """
    url_tpl = _PROVIDER_TEST_ENDPOINTS.get(provider)
    if not url_tpl:
        return False, f"Không có endpoint test cho provider '{provider}'."

    try:
        if provider == "gemini":
            url = url_tpl.format(key=key)
            req = _urllib_request.Request(url, method="GET")
            req.add_header("User-Agent", "PeiPei-AutoEdit/1.2.7")
            try:
                with _urllib_request.urlopen(req, timeout=6) as resp:
                    code = resp.getcode()
                    body = resp.read(200)
            except _urllib_error.HTTPError as e:
                code = e.code
                body = e.read(200) if e.fp else b""
            if code == 200:
                return True, (
                    f"✅ Gemini key hợp lệ.\n"
                    f"Endpoint: {_PROVIDER_TEST_ENDPOINTS['gemini'].split('?')[0]}\n"
                    f"HTTP {code} — server reachable."
                )
            if code in (400, 403):
                return False, f"❌ Sai API key cho Gemini (HTTP {code}). Vui lòng kiểm tra lại."
            return False, f"⚠️ HTTP {code}: {body[:100]!r}"

        if provider == "openai":
            req = _urllib_request.Request(url_tpl, method="GET")
            req.add_header("Authorization", f"Bearer {key}")
            req.add_header("User-Agent", "PeiPei-AutoEdit/1.2.7")
            try:
                with _urllib_request.urlopen(req, timeout=6) as resp:
                    code = resp.getcode()
                    body_preview = resp.read(200)
            except _urllib_error.HTTPError as e:
                code = e.code
                body_preview = e.read(200) if e.fp else b""
            if code == 200:
                return True, (
                    f"✅ OpenAI key hợp lệ.\n"
                    f"Endpoint: {url_tpl}\n"
                    f"HTTP {code} — server reachable."
                )
            if code in (401, 403):
                return False, f"❌ Sai API key cho OpenAI (HTTP {code})."
            return False, f"⚠️ HTTP {code}: {body_preview[:100]!r}"

        if provider == "anthropic":
            # Anthropic không có GET list endpoint hữu ích; POST 1 ping tối thiểu
            # với method nhỏ. Nếu 401/403 -> sai key. Nếu 200/4xx-not-401 -> server reachable.
            req = _urllib_request.Request(url_tpl, method="POST")
            req.add_header("x-api-key", key)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "PeiPei-AutoEdit/1.2.7")
            body = _json.dumps({"model": "claude-3-5-haiku-latest",
                                "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]}).encode("utf-8")
            try:
                with _urllib_request.urlopen(req, data=body, timeout=6) as resp:
                    code = resp.getcode()
            except _urllib_error.HTTPError as e:
                code = e.code
            if code in (200, 201):
                return True, f"✅ Anthropic key hợp lệ (HTTP {code} — ping OK)."
            if code in (401, 403):
                return False, f"❌ Sai API key cho Anthropic (HTTP {code})."
            if code in (400, 404, 429):
                # Sai body nhưng key đã auth được → consider OK
                return True, f"✅ Anthropic key xác thực được (HTTP {code} — body sai nhưng auth OK)."
            return False, f"⚠️ Anthropic HTTP {code}."

        return False, f"Provider '{provider}' không được hỗ trợ test."
    except _urllib_error.URLError as e:
        return False, f"🌐 Lỗi mạng: {e.reason}"
    except TimeoutError:
        return False, "⏱ Timeout (6s) — không phản hồi. Kiểm tra kết nối internet."
    except Exception as e:
        return False, f"❗ Lỗi không xác định: {e}"