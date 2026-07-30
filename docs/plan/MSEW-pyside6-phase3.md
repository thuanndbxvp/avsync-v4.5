# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 3

Tuân thủ nghiêm ngặt các bước dưới đây để thi công Tab Render Video.

## BƯỚC 1: Cập nhật CSS cho ScrollArea và CheckBox
Mở file `ui/style.qss` và **THÊM** đoạn CSS sau vào cuối file:
```css
/* --- ScrollArea & CheckBox (Phase 3) --- */
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QCheckBox {
    font-family: "Inter", sans-serif;
    color: #424656;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #DEE2E6;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #0066FF;
    border: 1px solid #0066FF;
}
```

## BƯỚC 2: Tạo Widget "RenderTab"
Tạo file mới `ui/tabs/tab_render.py` với nội dung sau:
```python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox, 
    QSpinBox, QRadioButton, QButtonGroup, QFileDialog, 
    QMessageBox, QScrollArea, QCheckBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt

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
        self.btn_render.clicked.connect(lambda: self.stub_action("Tiến hành Render Video..."))
        self.btn_preview.clicked.connect(lambda: self.stub_action("Chạy xem trước (Preview)..."))
        self.btn_queue.clicked.connect(lambda: self.stub_action("Thêm vào Hàng đợi..."))

        layout.addLayout(action_layout)
        layout.addStretch()

    def stub_action(self, msg):
        QMessageBox.information(self, "Đang xây dựng", f"{msg}\n(Tích hợp Backend ở Phase 4)")
```

## BƯỚC 3: Tích hợp RenderTab vào MainWindow
Mở file `ui/main_window.py` và thực hiện:

1. Thêm dòng import:
```python
from ui.tabs.tab_render import RenderTab
```

2. Cập nhật khối lệnh tạo tab trong hàm `setup_right_panel`:
**[Thay thế khối "Tạo 4 tab rỗng" cũ bằng:]**
```python
        # Tab 2: Render Video
        self.tab_render = RenderTab()
        self.stacked_widget.addWidget(self.tab_render)
        
        # Tạo 3 tab rỗng giữ chỗ cho các tab còn lại (Video ngủ, Hàng đợi, Cài đặt)
        for i in range(2, 5):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel(f"Đang chờ thi công Tab {i+1}... (Phase tiếp theo)"))
            self.stacked_widget.addWidget(page)
```

## BƯỚC 4: Kiểm định (Audit)
Tầng 2 chạy lệnh:
`python app.py`
Click sang Tab "Render Video". Thử lăn chuột (cuộn trang) xem cấu trúc trang dài có được QScrollArea xử lý tốt không. Click thử các nút bấm xem có bung hộp thoại thông báo không.
Nếu OK, báo cáo hoàn tất Phase 3!
