# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 5

Tuân thủ nghiêm ngặt các bước dưới đây để thi công Tab Cài đặt (Settings Tab).

## BƯỚC 1: Cập nhật CSS cho các thành phần Profile
Mở file `ui/style.qss` và **THÊM** đoạn CSS sau vào cuối file:
```css
/* --- Settings & Profiles (Phase 5) --- */
QTextEdit {
    background-color: #1E1E1E;
    color: #D4D4D4;
    border: none;
    font-family: "Consolas", monospace;
    font-size: 13px;
    padding: 8px;
}
QListWidget#ProfileList {
    background-color: #F8F9FA;
    border: none;
    border-right: 1px solid #DEE2E6;
}
QListWidget#ProfileList::item {
    padding: 10px;
    border-bottom: 1px solid #E9ECEF;
}
QListWidget#ProfileList::item:selected {
    background-color: #0066FF;
    color: white;
}
```

## BƯỚC 2: Tạo Widget "SettingsTab"
Tạo file mới `ui/tabs/tab_settings.py` với nội dung sau:
```python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox, 
    QMessageBox, QListWidget, QTextEdit, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Bọc toàn bộ vào ScrollArea vì tab Cài đặt có thể dài
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

        # ------------------- SECTION 1: CẤU HÌNH HỆ THỐNG -------------------
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
        btn_update.clicked.connect(lambda: self.stub_action("Kiểm tra cập nhật phần mềm..."))
        row1.addWidget(btn_update)
        layout1.addLayout(row1)
        layout.addWidget(card1)

        # ------------------- SECTION 2: API PROMPT -------------------
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)
        
        lbl_api = QLabel("🔑 API viết prompt — chọn nhà cung cấp")
        lbl_api.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout2.addWidget(lbl_api)
        
        grid_api = QGridLayout()
        grid_api.setColumnStretch(1, 1)
        grid_api.setVerticalSpacing(16)
        
        # Nhà cung cấp
        grid_api.addWidget(QLabel("Nhà cung cấp:"), 0, 0)
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(["Gemini", "OpenAI", "Anthropic"])
        grid_api.addWidget(self.cmb_provider, 0, 1)
        
        # Model
        grid_api.addWidget(QLabel("Model:"), 1, 0)
        row_model = QHBoxLayout()
        self.cmb_model = QComboBox()
        self.cmb_model.addItems(["gemini-3.5-flash", "gemini-pro"])
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        row_model.addWidget(self.cmb_model)
        row_model.addWidget(btn_refresh)
        grid_api.addLayout(row_model, 1, 1)
        
        # API Key
        grid_api.addWidget(QLabel("API Key:"), 2, 0)
        row_key = QHBoxLayout()
        self.inp_key = QLineEdit("*******************")
        self.inp_key.setEchoMode(QLineEdit.Password)
        self.btn_toggle_key = QPushButton("👁")
        self.btn_toggle_key.setFixedWidth(40)
        self.btn_toggle_key.setCheckable(True)
        self.btn_toggle_key.toggled.connect(self.toggle_api_key)
        row_key.addWidget(self.inp_key)
        row_key.addWidget(self.btn_toggle_key)
        grid_api.addLayout(row_key, 2, 1)
        
        layout2.addLayout(grid_api)
        
        row_api_btns = QHBoxLayout()
        btn_save_key = QPushButton("💾 Lưu key")
        btn_save_key.setStyleSheet("background-color: #0066FF; color: white; padding: 6px 12px; font-weight: bold; border-radius: 4px;")
        btn_test_conn = QPushButton("⚡ Kiểm tra kết nối")
        btn_save_key.clicked.connect(lambda: self.stub_action("Đã lưu API Key."))
        btn_test_conn.clicked.connect(lambda: self.stub_action("Kết nối API thành công!"))
        
        row_api_btns.addWidget(btn_save_key)
        row_api_btns.addWidget(btn_test_conn)
        row_api_btns.addStretch()
        layout2.addLayout(row_api_btns)
        
        layout.addWidget(card2)

        # ------------------- SECTION 3: STYLE VISUAL PROFILE -------------------
        card3 = QFrame()
        card3.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout3 = QVBoxLayout(card3)
        layout3.setContentsMargins(0, 0, 0, 0) # Bỏ viền để UI tràn đẹp
        
        lbl_style = QLabel("🎨 Style Visual Profile (cho từng kênh)")
        lbl_style.setStyleSheet("font-size: 16px; font-weight: bold; border: none; padding: 16px; background: #F8F9FA; border-bottom: 1px solid #DEE2E6;")
        layout3.addWidget(lbl_style)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Cột trái: List
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.list_profiles = QListWidget()
        self.list_profiles.setObjectName("ProfileList")
        self.list_profiles.addItems(["Người que", "Tâm linh", "Tài chính (Minimal)"])
        left_layout.addWidget(self.list_profiles)
        
        row_prof_btns = QHBoxLayout()
        row_prof_btns.setContentsMargins(8, 8, 8, 8)
        btn_add_prof = QPushButton("➕ Thêm")
        btn_del_prof = QPushButton("🗑 Xoá")
        btn_del_prof.setStyleSheet("color: #ba1a1a;")
        row_prof_btns.addWidget(btn_add_prof)
        row_prof_btns.addWidget(btn_del_prof)
        left_layout.addLayout(row_prof_btns)
        
        # Cột phải: Editor
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
        btn_save_prof = QPushButton("💾 Lưu profile này")
        btn_save_prof.setStyleSheet("background-color: #0066FF; color: white; padding: 6px 12px; border-radius: 4px;")
        row_editor_btns.addWidget(btn_preview_style)
        row_editor_btns.addWidget(btn_save_prof)
        right_layout.addLayout(row_editor_btns)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])
        
        # Set minimum height cho splitter
        splitter.setMinimumHeight(350)
        
        layout3.addWidget(splitter)
        layout.addWidget(card3)
        layout.addStretch()

    def toggle_api_key(self, checked):
        if checked:
            self.inp_key.setEchoMode(QLineEdit.Normal)
        else:
            self.inp_key.setEchoMode(QLineEdit.Password)

    def stub_action(self, msg):
        QMessageBox.information(self, "Hành động Cài đặt", msg)
```

## BƯỚC 3: Tích hợp SettingsTab vào MainWindow
Mở file `ui/main_window.py` và thực hiện:

1. Thêm dòng import:
```python
from ui.tabs.tab_settings import SettingsTab
```

2. Xóa bỏ hoàn toàn khối mã tạo tab giữ chỗ rỗng. Tại cuối hàm `setup_right_panel`, SỬA thành như sau:
**[Thay thế đoạn tạo tab rỗng bằng đoạn sau:]**
```python
        # Tab 5: Cài đặt
        self.tab_settings = SettingsTab()
        self.stacked_widget.addWidget(self.tab_settings)
        
        # Lúc này stacked_widget đã có đủ 5 tab thật!
```

## BƯỚC 4: Kiểm định (Audit)
Tầng 2 chạy lệnh `python app.py`. Click sang Tab "Cài đặt" để kiểm tra:
- Nút con mắt ở ô API Key có hoạt động ẩn/hiển text không.
- Splitter có thể kéo thả thay đổi kích thước danh sách Profile không.
Nếu pass, UI xem như ĐÃ HOÀN THIỆN 100%. Đóng Phase 5.
