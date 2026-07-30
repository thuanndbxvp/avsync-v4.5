# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 2 (REVISED)

Tuân thủ nghiêm ngặt các bước dưới đây.

## BƯỚC 1: Cập nhật CSS cho các form input
Mở file `ui/style.qss` và **THÊM** đoạn CSS sau vào cuối file:
```css
/* --- Form Inputs (Phase 2) --- */
QLineEdit, QComboBox, QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-radius: 4px;
    padding: 6px 12px;
    color: #191B24;
    font-family: "Inter", sans-serif;
    font-size: 13px;
    min-height: 20px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #0066FF;
    outline: none;
}

QRadioButton {
    font-family: "Inter", sans-serif;
    color: #424656;
    spacing: 8px;
}
```

## BƯỚC 2: Tạo Widget "PromptTab" (Xử lý toàn bộ Audit Issues)
Tạo file mới `ui/tabs/tab_prompt.py` với nội dung sau:
```python
# -*- coding: utf-8 -*-
import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox, 
    QSpinBox, QRadioButton, QButtonGroup, QFileDialog, QMessageBox
)

def load_config():
    """Tải config, có fallback an toàn nếu chưa có file."""
    fallback = {"profiles": {"Người que": "Mặc định", "Phong cách 3D": "Mặc định"}}
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.local.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                if "profiles" in data and len(data["profiles"]) > 0:
                    return data
        except Exception:
            pass
    return fallback

class PromptTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ------------------- CARD 1: NGUYÊN LIỆU -------------------
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)
        layout1.setContentsMargins(20, 20, 20, 20)
        
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

        # Tiêu đề
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

        # Style Profile
        lbl_profile = QLabel("Style Profile:")
        lbl_profile.setStyleSheet("border: none; font-weight: 500;")
        grid1.addWidget(lbl_profile, 3, 0)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(self.cfg.get("profiles", {}).keys()))
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
        layout2.setContentsMargins(20, 20, 20, 20)
        layout2.setSpacing(16)
        
        lbl_title2 = QLabel("⚙️ Tùy chọn Prompt chi tiết")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        row_secs = QHBoxLayout()
        lbl_secs = QLabel("Số giây mỗi cảnh:")
        lbl_secs.setStyleSheet("border: none; font-weight: 500;")
        self.spin_secs = QSpinBox()
        self.spin_secs.setRange(2, 3600)
        self.spin_secs.setValue(8)
        self.spin_secs.setFixedWidth(80)
        row_secs.addWidget(lbl_secs)
        row_secs.addWidget(self.spin_secs)
        row_secs.addStretch()
        layout2.addLayout(row_secs)

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
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #0066FF; 
                color: white; 
                padding: 12px 24px; 
                font-size: 14px;
                font-weight: bold; 
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #0052CC; }
        """)
        self.btn_create.clicked.connect(self.stub_make_prompts)
        
        self.btn_open = QPushButton("📄 Mở veo_prompts.txt")
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #E3F2FD; 
                color: #0066FF; 
                padding: 12px 24px; 
                font-size: 14px;
                font-weight: bold; 
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #BBDEFB; }
        """)
        self.btn_open.clicked.connect(self.stub_open_prompts)

        action_layout.addWidget(self.btn_create)
        action_layout.addWidget(self.btn_open)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        layout.addStretch()

    def browse_srt(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn file SRT", "", "SRT Files (*.srt);;All Files (*.*)")
        if file:
            self.srt_input.setText(file)

    def browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if folder:
            self.dir_input.setText(folder)
            
    def stub_make_prompts(self):
        # Stub cho Phase 4
        QMessageBox.information(self, "Đang xây dựng", "Logic gọi AI tạo Prompt sẽ được tích hợp từ app_legacy sang ở Phase 4 (Integration).")
        
    def stub_open_prompts(self):
        # Stub cho Phase 4
        QMessageBox.information(self, "Đang xây dựng", "Tính năng mở file sẽ được tích hợp ở Phase 4.")
```

## BƯỚC 3: Tích hợp PromptTab vào MainWindow
Mở file `ui/main_window.py`:

1. Thêm dòng import ở đầu file:
```python
from ui.tabs.tab_prompt import PromptTab
```

2. Tại hàm `setup_right_panel`, tìm đến dòng `self.stacked_widget = QStackedWidget()` và THAY THẾ khối mã tạo 5 tab rỗng bằng:
```python
        # Main Canvas (Tabs)
        self.stacked_widget = QStackedWidget()
        self.right_layout.addWidget(self.stacked_widget, 1)
        
        # Tab 1: Tạo Prompt
        self.tab_prompt = PromptTab()
        self.stacked_widget.addWidget(self.tab_prompt)
        
        # Tạo 4 tab rỗng giữ chỗ cho các tab còn lại
        for i in range(1, 5):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel(f"Đang chờ thi công Tab {i+1}... (Phase tiếp theo)"))
            self.stacked_widget.addWidget(page)
```

## BƯỚC 4: Kiểm định (Audit)
Chạy lệnh `python app.py`. 
Click "Tạo Prompt" -> Test bấm 2 nút chức năng xem có hiện MessageBox không.
Kiểm tra combobox "Style Profile" xem đã có data chưa.
Nếu PASS, đóng task Phase 2.
