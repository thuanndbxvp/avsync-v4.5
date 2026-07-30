# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 4

Tuân thủ nghiêm ngặt các bước dưới đây để thi công Tab Video Ngủ và Tab Hàng Đợi.

## BƯỚC 1: Cập nhật CSS cho Danh sách (Lists & Tables)
Mở file `ui/style.qss` và **THÊM** đoạn CSS sau vào cuối file:
```css
/* --- Lists & Tables (Phase 4) --- */
QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-radius: 8px;
    font-family: "Inter", sans-serif;
    color: #191B24;
}
QHeaderView::section {
    background-color: #F2F3FF;
    color: #424656;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #DEE2E6;
    font-weight: bold;
}
```

## BƯỚC 2: Tạo Widget "SleepTab" (Tab Video Ngủ)
Tạo file mới `ui/tabs/tab_sleep.py` với nội dung sau:
```python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox, 
    QSpinBox, QMessageBox, QDoubleSpinBox
)

class SleepTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ------------------- CARD 1: ĐẦU VÀO FILE -------------------
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)
        
        lbl_title1 = QLabel("📁 Khu vực Đầu vào File (Video ngủ dài 3-4 tiếng)")
        lbl_title1.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout1.addWidget(lbl_title1)

        grid1 = QGridLayout()
        grid1.setColumnStretch(1, 1)

        inputs = [
            ("NỀN (clip / ảnh):", "backgrounds"),
            ("AUDIO dài (kịch bản):", "scripts"),
            ("Âm thanh NỀN (tùy chọn):", ""),
            ("Xuất ra MP4:", "sleep.mp4")
        ]
        
        for row, (label_text, default_val) in enumerate(inputs):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("border: none; font-weight: bold;")
            inp = QLineEdit(default_val)
            btn = QPushButton("Chọn...")
            btn.setStyleSheet("background: #F8F9FA; border: 1px solid #DEE2E6; padding: 4px 10px; border-radius: 4px;")
            btn.clicked.connect(lambda checked, msg=f"Mở chọn {label_text}": self.stub_action(msg))
            
            box = QHBoxLayout()
            box.addWidget(inp)
            box.addWidget(btn)
            
            grid1.addWidget(lbl, row, 0)
            grid1.addLayout(box, row, 1)
            
        layout1.addLayout(grid1)
        layout.addWidget(card1)

        # ------------------- CARD 2: TÙY CHỌN -------------------
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)
        
        lbl_title2 = QLabel("⚙ Tùy chọn Cảnh & Hiệu ứng")
        lbl_title2.setStyleSheet("font-size: 16px; font-weight: bold; color: #191B24; border: none;")
        layout2.addWidget(lbl_title2)

        row_opt = QHBoxLayout()
        row_opt.addWidget(QLabel("Hiệu ứng (Ảnh tĩnh):"))
        self.cmb_fx = QComboBox()
        self.cmb_fx.addItems(["none", "vừa", "nhẹ", "mạnh"])
        row_opt.addWidget(self.cmb_fx)
        
        row_opt.addWidget(QLabel(" Fade tiếng (s):"))
        self.spin_fade = QSpinBox()
        self.spin_fade.setValue(4)
        row_opt.addWidget(self.spin_fade)
        
        row_opt.addWidget(QLabel(" Visualizer:"))
        self.cmb_vis = QComboBox()
        self.cmb_vis.addItems(["none", "bars", "waves"])
        row_opt.addWidget(self.cmb_vis)
        row_opt.addStretch()
        layout2.addLayout(row_opt)

        layout.addWidget(card2)

        # ------------------- 3. ACTION AREA -------------------
        action_layout = QHBoxLayout()
        self.btn_render = QPushButton("🕒 TẠO VIDEO NGỦ")
        self.btn_render.setStyleSheet("background-color: #0066FF; color: white; padding: 12px 24px; font-weight: bold; border-radius: 6px;")
        self.btn_render.clicked.connect(lambda: self.stub_action("Tiến hành render Video Ngủ..."))
        
        action_layout.addWidget(self.btn_render)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        layout.addStretch()

    def stub_action(self, msg):
        QMessageBox.information(self, "Thông báo", f"{msg}\n(Tích hợp ở Phase 4/5)")
```

## BƯỚC 3: Tạo Widget "QueueTab" (Tab Hàng Đợi)
Tạo file mới `ui/tabs/tab_queue.py` với nội dung sau:
```python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox
)

class QueueTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # --- PANEL 1: HÀNG ĐỢI ---
        card1 = QFrame()
        card1.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout1 = QVBoxLayout(card1)
        
        lbl_queue = QLabel("📋 0 video trong hàng đợi")
        lbl_queue.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout1.addWidget(lbl_queue)
        
        self.list_queue = QListWidget()
        self.list_queue.addItem("Chưa có video nào trong hàng đợi.")
        layout1.addWidget(self.list_queue)
        
        row_q_btn = QHBoxLayout()
        btn_del = QPushButton("Xóa mục chọn")
        btn_clear = QPushButton("Xóa hết")
        btn_render_all = QPushButton("▶ RENDER CẢ HÀNG ĐỢI")
        btn_render_all.setStyleSheet("background-color: #0066FF; color: white; padding: 8px 16px; font-weight: bold; border-radius: 4px;")
        
        for btn in [btn_del, btn_clear, btn_render_all]:
            btn.clicked.connect(lambda checked, text=btn.text(): self.stub_action(f"Bấm: {text}"))
            
        row_q_btn.addWidget(btn_del)
        row_q_btn.addWidget(btn_clear)
        row_q_btn.addStretch()
        row_q_btn.addWidget(btn_render_all)
        layout1.addLayout(row_q_btn)
        
        layout.addWidget(card1, 1)

        # --- PANEL 2: LỊCH SỬ ---
        card2 = QFrame()
        card2.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; }")
        layout2 = QVBoxLayout(card2)
        
        lbl_history = QLabel("🕒 Lịch sử render")
        lbl_history.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout2.addWidget(lbl_history)
        
        self.table_history = QTableWidget(0, 2)
        self.table_history.setHorizontalHeaderLabels(["Ngày giờ", "Tên file"])
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout2.addWidget(self.table_history)
        
        row_h_btn = QHBoxLayout()
        btn_open = QPushButton("Mở thư mục")
        btn_clear_h = QPushButton("Xóa lịch sử")
        
        for btn in [btn_open, btn_clear_h]:
            btn.clicked.connect(lambda checked, text=btn.text(): self.stub_action(f"Bấm: {text}"))
            row_h_btn.addWidget(btn)
        row_h_btn.addStretch()
        layout2.addLayout(row_h_btn)
        
        layout.addWidget(card2, 1)

    def stub_action(self, msg):
        QMessageBox.information(self, "Thông báo", f"{msg}\n(Backend chờ Tích hợp)")
```

## BƯỚC 4: Tích hợp 2 Tab vào MainWindow
Mở file `ui/main_window.py` và thực hiện:

1. Thêm dòng import:
```python
from ui.tabs.tab_sleep import SleepTab
from ui.tabs.tab_queue import QueueTab
```

2. Cập nhật khối lệnh tạo tab trong hàm `setup_right_panel`:
**[Thay thế khối "Tạo 3 tab rỗng" cũ bằng:]**
```python
        # Tab 3: Video Ngủ
        self.tab_sleep = SleepTab()
        self.stacked_widget.addWidget(self.tab_sleep)
        
        # Tab 4: Hàng Đợi
        self.tab_queue = QueueTab()
        self.stacked_widget.addWidget(self.tab_queue)
        
        # Tạo 1 tab rỗng giữ chỗ cho Tab Cài đặt (Tab số 5)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Đang chờ thi công Tab Cài đặt... (Phase cuối)"))
        self.stacked_widget.addWidget(page)
```

## BƯỚC 5: Kiểm định (Audit)
Tầng 2 chạy lệnh:
`python app.py`
Click sang Tab "Video ngủ" và "Hàng đợi" để kiểm tra giao diện. Thử bấm các nút.
Nếu OK, báo cáo hoàn tất Phase 4!
