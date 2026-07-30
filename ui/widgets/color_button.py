"""ui.widgets.color_button — Custom QPushButton cho Color Picker.

Khi user click -> mở QColorDialog. Sau khi chọn:
  - Đổi màu nền nút (preview)
  - Lưu hex vào self.hex_value
  - Emit `color_changed(str)` signal

Helper nhỏ gọn — dùng được trong mọi tab. ZERO side-effect ngoài UI.
"""
from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QColorDialog
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal


class ColorButton(QPushButton):
    """Nút bấm hiện bảng màu — pick rồi đổi background + emit hex."""

    color_changed = Signal(str)  # emits "#RRGGBB" sau khi user chọn

    def __init__(self, initial_hex: str = "#FFFFFF", parent=None, title: str = "Chọn màu"):
        super().__init__(parent)
        self.hex_value = initial_hex
        self._title = title
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        """Đổi background + foreground (tùy contrast) để user thấy được màu đã chọn."""
        try:
            c = QColor(self.hex_value)
        except Exception:
            c = QColor("#FFFFFF")
        # Compute brightness để quyết định chữ đen/trắng (đọc label rõ)
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        text_color = "#000000" if brightness > 128 else "#FFFFFF"
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self.hex_value}; color: {text_color};"
            f" border: 1px solid #CCCCCC; padding: 6px 12px; border-radius: 4px;"
            f" font-weight: 500; min-width: 80px; }}"
            f"QPushButton:hover {{ border: 2px solid #0066FF; }}"
        )
        # Cập nhật tooltip + text fallback (nếu nền quá tối thì text trắng bị mất)
        self.setText(self.hex_value.upper())
        self.setToolTip(f"{self._title}\nMã: {self.hex_value}")

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.hex_value), self, self._title)
        if c.isValid():
            self.hex_value = c.name()
            self._update_style()
            self.color_changed.emit(self.hex_value)

    def set_hex(self, hex_value: str):
        """Set programmatic (không qua dialog) — dùng khi load config."""
        self.hex_value = hex_value
        self._update_style()