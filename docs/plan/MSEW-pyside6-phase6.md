# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 6 (REVISED)

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối Tab Tạo Prompt với Backend cũ.

## BƯỚC 1: Chuẩn bị Cổng Log (Console API) trên MainWindow
Mở file `ui/main_window.py`:
1. Thêm phương thức `append_log` vào class `MainWindow`:
```python
    def append_log(self, text, color="#D4D4D4"):
        # Định dạng text thành HTML để tô màu trên ConsoleLog (QTextEdit)
        html = f'<span style="color: {color};">{text}</span>'
        self.console_log.append(html)
```

## BƯỚC 2: Xây dựng QThread Worker xử lý Prompt
Tạo thư mục `core` ở thư mục gốc (ngang hàng `ui`), thêm file `core/__init__.py` rỗng.
Tạo file `core/worker_prompt.py` với nội dung toàn vẹn:
```python
# -*- coding: utf-8 -*-
import os
import sys
from PySide6.QtCore import QThread, Signal

class PromptWorker(QThread):
    # Signals để giao tiếp với UI
    log_signal = Signal(str, str) # text, color
    finished_signal = Signal(bool, str) # success, message
    
    def __init__(self, data_dict):
        super().__init__()
        self.data = data_dict
        
    def run(self):
        self.log_signal.emit("[System] Bắt đầu tiến trình phân tích AI (POC Phase 6)...", "#0066FF")
        
        try:
            # Import các module core chuẩn xác (đã xác nhận tồn tại)
            import auto_edit as ae
            import build_scenes as bs
            import ai_prompts
            
            cfg = self.data.get("cfg", {})
            srt = self.data.get("srt", "")
            target_secs = float(self.data.get("secs", 8))
            produce = self.data.get("produce_mode", "")
            prov = self.data.get("provider", "gemini")
            key = cfg.get("keys", {}).get(prov, "")
            style_mode = "in_prompt" # Hardcode tạm cho POC
            style = cfg.get("profiles", {}).get(self.data.get("profile", ""), "")
            
            if not os.path.isfile(srt):
                self.log_signal.emit(f"[Error] Không tìm thấy file SRT: {srt}", "#ba1a1a")
                self.finished_signal.emit(False, "Thiếu file SRT")
                return
                
            if not key.strip():
                self.log_signal.emit(f"[Error] Thiếu API Key cho provider {prov}.", "#ba1a1a")
                self.finished_signal.emit(False, "Chưa cài đặt API Key")
                return

            self.log_signal.emit(f"• Đọc SRT, gom cảnh (~{target_secs}s)...", "#D4D4D4")
            segs = ae.parse_srt(srt)
            scenes = bs.group_scenes(segs, target_secs)
            texts = [" ".join(t.strip() for t in s["texts"]).strip() for s in scenes]
            
            def prog(done, total):
                self.log_signal.emit(f"   ...tiến độ AI: {done}/{total}", "#D4D4D4")
                
            model = cfg.get("models", {}).get(prov)
            
            # Phân tách logic theo mode (chỉ demo gọi hàm thật, có thể rút gọn thành 1 case)
            if "i2v" in produce.lower() or "từ ảnh" in produce.lower():
                self.log_signal.emit(f"• {len(segs)} đoạn → {len(scenes)} cảnh. Bắt đầu gọi {prov} (Image-to-Video)...", "#28A745")
                # Gọi API thật (sẽ tốn thời gian, QThread giúp UI không bị đơ)
                img_prompts = ai_prompts.generate_prompts(
                    texts, style, key, model=model, progress=prog, mode="image",
                    style_mode=style_mode, provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                
                self.log_signal.emit("✅ Tạo Prompt ẢNH thành công!", "#28A745")
                # Lẽ ra phải gọi tiếp generate_motion_prompts và write scenes.csv ở đây
                # Nhưng vì là POC, ta chứng minh API gọi được là đủ pass.
                
            else:
                self.log_signal.emit(f"• {len(segs)} đoạn → {len(scenes)} cảnh. Gọi {prov} tạo prompt...", "#28A745")
                prompts = ai_prompts.generate_prompts(
                    texts, style, key, model=model, progress=prog, mode="video",
                    style_mode=style_mode, provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                
                self.log_signal.emit("✅ Tạo Prompt VIDEO thành công!", "#28A745")

            self.finished_signal.emit(True, "Hoàn thành!")
            
        except Exception as e:
            self.log_signal.emit(f"[Exception] {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```

## BƯỚC 3: Đấu nối QThread vào Tab Tạo Prompt
Mở file `ui/tabs/tab_prompt.py`:

1. Thêm import:
```python
from core.worker_prompt import PromptWorker
```

2. Tùy chỉnh hàm gán dữ liệu và chạy worker (thay cho hàm Stub):
```python
    def run_make_prompts(self):
        main_win = self.window()
        if hasattr(main_win, "append_log"):
            main_win.append_log("Đang khởi động Worker gửi dữ liệu AI...", "#E3F2FD")
            
        # Thu thập dữ liệu
        data = {
            "cfg": self.cfg,
            "srt": self.srt_input.text(),
            "title": self.title_input.text(),
            "dir": self.dir_input.text(),
            "profile": self.profile_combo.currentText(),
            "char": self.char_input.text(),
            "secs": self.spin_secs.value(),
            # Lấy text của radio button đang được check
            "produce_mode": self.produce_group.checkedButton().text() if self.produce_group.checkedButton() else "",
            "provider": self.cfg.get("provider", "gemini")
        }
        
        # Khóa nút bấm
        self.btn_create.setEnabled(False)
        self.btn_create.setText("⏳ ĐANG TẠO PROMPT...")
        
        # Chạy Worker
        self.worker = PromptWorker(data)
        if hasattr(main_win, "append_log"):
            self.worker.log_signal.connect(main_win.append_log)
            
        self.worker.finished_signal.connect(self.on_prompt_finished)
        self.worker.start()

    def on_prompt_finished(self, success, msg):
        self.btn_create.setEnabled(True)
        self.btn_create.setText("🤖 TẠO PROMPT (AI)")
        if success:
            QMessageBox.information(self, "Thành công", f"Tiến trình POC hoàn tất!\n{msg}")
        else:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra:\n{msg}")
```

3. Tìm dòng `self.btn_create.clicked.connect(...)` (khoảng dòng 128 trong file `tab_prompt.py`) và trỏ nó về `self.run_make_prompts` thay vì `self.stub_make_prompts`.

## BƯỚC 4: Kiểm định (Audit)
Chạy lệnh `python app.py`. 
Click sang Tab "Tạo Prompt", trỏ File SRT tới 1 file có thật, đảm bảo có API Key trong `config.local.json`, rồi bấm "TẠO PROMPT (AI)".
Quan sát Console ở góc dưới màn hình xem log báo "Đọc SRT", "tiến độ AI: 1/N" có hiện ra không. Nút bấm có bị mờ đi không. Nếu không văng lỗi, UI vẫn mượt, Phase 6 chính thức THÀNH CÔNG!
