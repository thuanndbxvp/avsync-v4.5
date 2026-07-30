# MICRO-STEP EXECUTION WORKFLOW: REFACTOR MILESTONE 1

Tuân thủ nghiêm ngặt các bước dưới đây để bóc tách Domain & Infrastructure. Đảm bảo Zero Regression (sau khi làm xong code cũ vẫn phải chạy đúng).

## BƯỚC 1: Xây dựng Domain Layer (Tầng Logic thuần)
1. Tạo thư mục `domain/` và file `domain/__init__.py`.
2. Tạo file `domain/timeline.py`:
   - Cut các hàm `_ass_time`, `parse_srt`, `group_scenes` từ `auto_edit.py` và `build_scenes.py` đưa vào đây.
   - Chỉnh sửa lại các import cần thiết bên trong file này.
3. Tạo file `domain/visual_style.py`:
   - Cut các hàm parsing style từ `ai_prompts.py` (như `_style_caption`, `_style_for_ai`, v.v.) đưa vào đây.

## BƯỚC 2: Xây dựng Infrastructure Layer (Tầng I/O)
1. Tạo thư mục `infrastructure/` và `infrastructure/__init__.py`.
2. Tạo file `infrastructure/shell_runner.py`:
   - Tạo hàm `run_cmd(args, timeout=None)` bọc lại `subprocess.run()`.
3. Tạo file `infrastructure/filesystem.py`:
   - Bóc tách các đoạn tìm kiếm file ảnh/media (chức năng `collect_media` trong `auto_edit.py`) vào đây.

## BƯỚC 3: Re-export (Giữ mạng sống cho code cũ)
1. Mở `auto_edit.py`. Do ta đã move `parse_srt` đi, hãy thêm dòng: `from domain.timeline import parse_srt` để code CLI cũ vẫn thấy được hàm này.
2. Áp dụng tương tự cho `build_scenes.py` và `ai_prompts.py` (Import ngược lại từ `domain/`).

## BƯỚC 4: Kiểm định (Audit)
- Chạy lệnh CLI cũ: `python build_scenes.py --srt input/subtitle.srt` (nếu có srt) hoặc test thử chức năng Render/Prompt trên UI. Nếu mọi thứ vẫn chạy trơn tru, Milestone 1 thành công!
