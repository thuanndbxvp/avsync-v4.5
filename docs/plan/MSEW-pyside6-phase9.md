# MICRO-STEP EXECUTION WORKFLOW: PYSIDE6 PHASE 9

Tuân thủ nghiêm ngặt các bước dưới đây để đấu nối (Wire) thật tính năng Render Video, đảm bảo KHÔNG làm hỏng code cũ (Zero regression).

## BƯỚC 1: Bóc tách logic trong `auto_edit.py`
Mở file `auto_edit.py`:
1. Tìm đến khối lệnh cuối cùng (thường là `def main():` hoặc `if __name__ == "__main__":`).
2. Khối này hiện đang dùng `argparse` để lấy biến `args.srt`, `args.images`, `args.out`, sau đó tiến hành tạo thư mục temp, gọi `parse_srt`, gọi ffmpeg...
3. **Tách toàn bộ logic xử lý đó** (từ lúc bắt đầu chạy parse_srt cho tới lúc báo "XONG") ra thành một function độc lập bên ngoài:
```python
def render_video(srt_path, img_dir, out_path, cfg=None, progress_cb=None):
    """
    Hàm lõi render video. 
    cfg: dictionary cấu hình.
    progress_cb: callback dạng progress_cb("Nội dung log") để bắn log lên UI.
    """
    # Thay thế các lệnh in bằng print cũ thành progress_cb (nếu có)
    def log(msg):
        if progress_cb:
            progress_cb(msg)
        else:
            print(msg)
            
    log(f"Bắt đầu render: SRT={srt_path}, IMG={img_dir}, OUT={out_path}")
    
    # [LƯU Ý CỦA PLANNER]: Tầng 2 BÊ NGUYÊN logic cũ vào đây.
    # Nhớ thay thế các biến args.srt thành srt_path, args.images thành img_dir...
    # ... code xử lý ffmpeg, build_scenes, v.v...
    
    log("Render hoàn tất!")
    return True
```
4. Ở khối `if __name__ == "__main__":` (hoặc `def main()`), thay vì chứa logic như cũ, bây giờ chỉ còn:
```python
    args = parser.parse_args()
    # Build cfg từ args (nếu cần)
    render_video(args.srt, args.images, args.out, cfg={}, progress_cb=None)
```

## BƯỚC 2: Cập nhật `core/worker_render.py`
Mở file `core/worker_render.py` (đã tạo ở Phase 8) và thay đoạn POC bằng đoạn gọi thật:
```python
        try:
            import auto_edit as ae
            # Bóc tách thông tin từ data_dict
            cfg = self.data.get("cfg", {})
            srt = self.data.get("srt", "")
            img_dir = self.data.get("img_dir", "")
            output = self.data.get("output", "")
            
            self.log_signal.emit(f"• Chuẩn bị ghép video: {output}", "#D4D4D4")
            
            # Hàm callback truyền tiến độ
            def prog(msg):
                self.log_signal.emit(f"   {msg}", "#D4D4D4")
                
            # GỌI HÀM THẬT VỪA TẠO Ở BƯỚC 1
            ae.render_video(srt, img_dir, output, cfg, progress_cb=prog)
            
            self.log_signal.emit("✅ Đã hoàn tất Render Video!", "#28A745")
            self.finished_signal.emit(True, "Render Video hoàn tất!")
            
        except Exception as e:
            self.log_signal.emit(f"[Exception] Lỗi render: {str(e)}", "#ba1a1a")
            self.finished_signal.emit(False, str(e))
```

## BƯỚC 3: Kiểm định (Audit)
Chạy lệnh `python app.py`. 
Vào Tab Render Video, nhập các đường dẫn chính xác tới 1 file SRT, thư mục chứa ảnh (đã đánh số 01.png, 02.png) và chọn Tên file ra. 
Bấm **RENDER VIDEO**.
Nếu ứng dụng không đơ cứng, Console Log hiện các dòng xuất ra từ `ffmpeg` (thông qua `progress_cb`), và cuối cùng thư mục output sinh ra file MP4 xem được bình thường, Phase 9 đã thành công rực rỡ!
