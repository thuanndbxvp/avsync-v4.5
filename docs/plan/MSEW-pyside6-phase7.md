# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 7

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối (Wire) thật tính năng Tạo Prompt bằng các API lõi của hệ thống.

## BƯỚC 1: Sửa đổi core/worker_prompt.py
Mở file `core/worker_prompt.py` và SỬA TOÀN BỘ file thành nội dung sau:
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
        self.log_signal.emit("[System] Bắt đầu tiến trình phân tích AI (Phase 7 - Real Wiring)...", "#0066FF")
        
        try:
            # Import các module core chuẩn xác của ứng dụng cũ
            import auto_edit as ae
            import build_scenes as bs
            import ai_prompts
            
            cfg = self.data.get("cfg", {})
            srt = self.data.get("srt", "")
            target_secs = float(self.data.get("secs", 8))
            produce = self.data.get("produce_mode", "")
            prov = self.data.get("provider", "gemini")
            key = cfg.get("keys", {}).get(prov, "")
            
            # Khớp với UI radio buttons
            style_mode = "in_prompt" 
            style = cfg.get("profiles", {}).get(self.data.get("profile", ""), "")
            
            if not os.path.isfile(srt):
                self.log_signal.emit(f"[Error] Không tìm thấy file SRT: {srt}", "#ba1a1a")
                self.finished_signal.emit(False, "Thiếu file SRT")
                return
                
            if not key.strip():
                self.log_signal.emit(f"[Error] Thiếu API Key cho provider {prov}.", "#ba1a1a")
                self.finished_signal.emit(False, "Chưa cấu hình API Key")
                return

            self.log_signal.emit(f"• Đọc SRT, gom cảnh (~{target_secs}s)...", "#D4D4D4")
            segs = ae.parse_srt(srt)
            scenes = bs.group_scenes(segs, target_secs)
            texts = [" ".join(t.strip() for t in s["texts"]).strip() for s in scenes]
            
            def prog(done, total):
                self.log_signal.emit(f"   ...tiến độ AI: {done}/{total}", "#D4D4D4")
                
            model = cfg.get("models", {}).get(prov)
            
            # Dựa vào mode sản xuất
            is_i2v = "clip từ ảnh" in produce.lower()
            is_chain = "ảnh đầu→cuối" in produce.lower()
            
            if is_i2v:
                self.log_signal.emit(f"• {len(segs)} đoạn → {len(scenes)} cảnh. Gọi {prov} (Image-to-Video)...", "#28A745")
                self.log_signal.emit("• (1/2) Viết prompt ẢNH keyframe...", "#D4D4D4")
                img_prompts = ai_prompts.generate_prompts(
                    texts, style, key, model=model, progress=prog, mode="image",
                    style_mode=style_mode, provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                
                self.log_signal.emit("• (2/2) Viết prompt CHUYỂN ĐỘNG...", "#D4D4D4")
                motion = ai_prompts.generate_motion_prompts(
                    texts, key, image_prompts=img_prompts, model=model, progress=prog,
                    provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                    
                self.log_signal.emit("✅ Tạo Prompt ẢNH & CHUYỂN ĐỘNG thành công!", "#28A745")
                
            elif is_chain:
                self.log_signal.emit(f"• {len(scenes)} cảnh → Gọi {prov} tạo chuỗi ảnh liên hoàn...", "#28A745")
                img_prompts, motion = ai_prompts.generate_chain_prompts(
                    texts, style, key, model=model, progress=prog,
                    style_mode=style_mode, provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                
                self.log_signal.emit("✅ Tạo Prompt Chuỗi thành công!", "#28A745")
                
            else:
                mode_str = "image" if "ảnh tĩnh" in produce.lower() else "video"
                self.log_signal.emit(f"• {len(segs)} đoạn → {len(scenes)} cảnh. Gọi {prov} tạo prompt {mode_str.upper()}...", "#28A745")
                prompts = ai_prompts.generate_prompts(
                    texts, style, key, model=model, progress=prog, mode=mode_str,
                    style_mode=style_mode, provider=prov, character=self.data.get("char", ""), title=self.data.get("title", ""))
                
                self.log_signal.emit(f"✅ Tạo Prompt {mode_str.upper()} thành công!", "#28A745")

            self.finished_signal.emit(True, "Quá trình Tạo Prompt Backend hoàn tất!")
            
        except Exception as e:
            self.log_signal.emit(f"[Exception] {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```

## BƯỚC 2: Kiểm định (Audit)
Chạy lệnh `python app.py`. 
1. Vào tab Cài đặt, đảm bảo đã điền API Key.
2. Sang Tab Tạo Prompt, trỏ File SRT tới file `subtitle.srt` có sẵn (nếu có) hoặc tạo 1 file `test.srt` mẫu.
3. Bấm TẠO PROMPT. 
4. Console Log phải hiện "Đọc SRT", và sau đó thông báo gọi hàm API thực tế.
Nếu API trả về kết quả (hoặc lỗi kết nối mạng chính đáng từ Gemini/OpenAI), thì tích hợp Backend đã 100% thành công!
