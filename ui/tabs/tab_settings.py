# -*- coding: utf-8 -*-
"""ui.tabs.tab_settings — Settings tab (M6: wire ConfigService cho persistence).

Các tính năng wired đến ConfigService (services/config_service.py):
  - Save API key (per provider)
  - Refresh model list theo provider
  - Save / Add / Delete Style Profile
  - Load lúc init từ file
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QListWidget, QTextEdit, QScrollArea, QSplitter, QInputDialog,
)
from PySide6.QtCore import Qt

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
        row1.addWidget(self.cmb_lang)
        btn_update = QPushButton("Kiểm tra cập nhật")
        btn_update.clicked.connect(self._stub_msg("Kiểm tra cập nhật phần mềm..."))
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
        btn_add_prof = QPushButton("➕ Thêm")
        btn_add_prof.clicked.connect(self._add_profile)
        btn_del_prof = QPushButton("🗑 Xoá")
        btn_del_prof.setStyleSheet("color: #ba1a1a;")
        btn_del_prof.clicked.connect(self._del_profile)
        row_prof_btns.addWidget(btn_add_prof)
        row_prof_btns.addWidget(btn_del_prof)
        left_layout.addLayout(row_prof_btns)

        # Right: editor + save
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

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

        self._refresh_profile_list()

    def _refresh_profile_list(self):
        """Reload list_profiles từ self._data['profiles']."""
        self.list_profiles.clear()
        profiles = self._data.get("profiles", {})
        for name in profiles.keys():
            self.list_profiles.addItem(name)

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
        provider = self.cmb_provider.currentText()
        key = self.inp_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Thiếu key",
                                f"Chưa nhập API key cho '{provider}'. Vui lòng nhập và Lưu trước.")
            return
        # Đơn giản: báo OK + format check. Không gọi API thật để tránh latency.
        if len(key) < 8:
            QMessageBox.warning(self, "Key lỗi",
                                f"API key quá ngắn (chỉ {len(key)} ký tự). Vui lòng kiểm tra lại.")
            return
        QMessageBox.information(self, "Kết nối OK",
                                f"API key '{provider}' hợp lệ (≥{len(key)} ký tự). "
                                f"(Mock test — kết nối thật sẽ chạy khi bấm TẠO PROMPT).")

    def _toggle_api_key(self, checked):
        self.inp_key.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    # Profile
    def _on_profile_select(self, current, previous):
        """Khi user chọn 1 profile trong list → load text vào editor."""
        if current is None:
            return
        name = current.text()
        text = self._data.get("profiles", {}).get(name, "")
        self.txt_prompt.setPlainText(text)

    def _save_profile(self):
        """Lưu nội dung editor vào profile đang chọn (hoặc tạo mới nếu trống)."""
        current = self.list_profiles.currentItem()
        if current is None:
            # Chưa chọn gì → coi như ADD mới
            self._add_profile()
            return
        name = current.text()
        text = self.txt_prompt.toPlainText().strip()
        self._data["profiles"][name] = text
        self.cfg.save(self._data)
        QMessageBox.information(self, "Đã lưu", f"Đã lưu profile '{name}'.")

    def _add_profile(self):
        name, ok = QInputDialog.getText(self, "Thêm Profile", "Tên profile mới:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._data.get("profiles", {}):
            QMessageBox.warning(self, "Trùng tên",
                                f"Profile '{name}' đã tồn tại. Dùng Lưu thay vì Thêm.")
            return
        self._data["profiles"][name] = self.txt_prompt.toPlainText().strip()
        self.cfg.save(self._data)
        self._refresh_profile_list()
        # Select profile mới
        items = self.list_profiles.findItems(name, Qt.MatchExactly)
        if items:
            self.list_profiles.setCurrentItem(items[0])

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

    # ---------------------------------------------------------------- helpers
    def _stub_msg(self, msg):
        """Closure trả về slot in MessageBox — cho các nút chưa wire (cập nhật...)."""
        def slot():
            QMessageBox.information(self, "Thông báo", msg)
        return slot