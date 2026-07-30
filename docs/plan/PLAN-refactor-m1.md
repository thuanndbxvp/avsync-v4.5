# KIẾN TRÚC TỔNG QUAN: CORE REFACTORING (MILESTONE 1)

## MỤC TIÊU CỦA PLANNER
Milestone 1 (M1) là bước đặt nền móng kiến trúc Clean Architecture. Mục tiêu là bóc tách toàn bộ logic tính toán thuần túy (Domain Logic) và lớp tương tác hệ thống (Infrastructure) ra khỏi các file "God Object" như `auto_edit.py`. 

## NHIỆM VỤ CỐT LÕI
1. **Tạo lớp Domain (`domain/`)**: 
   - Không chứa bất kỳ I/O nào (không gọi thư viện os, subprocess, request).
   - Di chuyển các hàm tính toán thời gian, parsing SRT, gom nhóm cảnh từ `build_scenes.py` và `auto_edit.py` vào `domain/timeline.py`.
   - Bóc tách các hàm cấu hình giao diện text, style thành `domain/visual_style.py`.
2. **Tạo lớp Infrastructure (`infrastructure/`)**:
   - Chứa các logic gọi I/O (subprocess ffmpeg, probe).
   - Tạo file `shell_runner.py` để bọc lại `subprocess.run`.
3. **Chiến lược Strangler Pattern**:
   - `auto_edit.py` và `build_scenes.py` hiện tại KHÔNG bị xóa. Nó sẽ import các hàm từ `domain/` và `infrastructure/` để tiếp tục hoạt động như cũ. (Đảm bảo Zero Regression).

## CÁC FILE CẦN CAN THIỆP
- Thư mục mới: `domain/`, `infrastructure/`
- Chỉnh sửa nhẹ: `auto_edit.py`, `build_scenes.py`, `ai_prompts.py` (Re-export logic).
