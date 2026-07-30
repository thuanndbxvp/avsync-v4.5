# KIẾN TRÚC TỔNG QUAN: CORE REFACTORING (MILESTONE 2)

## MỤC TIÊU CỦA PLANNER
Milestone 2 (M2) nhắm trực tiếp vào nút thắt cổ chai về mạng: **Tạo Prompt AI**. Thay vì gửi từng Request cho từng cảnh một cách tuần tự (rất chậm), chúng ta sẽ gom nhóm thành các Batch và gọi API song song (Concurrent Requests) thông qua AsyncIO. Điều này giúp tốc độ tạo Prompt có thể nhanh gấp 5 lần.

## NHIỆM VỤ CỐT LÕI
1. **Infrastructure (Hạ tầng AI Async)**:
   - Tạo `infrastructure/ai_pool.py` để chứa `AsyncAIPool`. Sử dụng `asyncio.Semaphore` để giới hạn số lượng Request đồng thời (tránh bị Rate Limit 429).
   - Tích hợp httpx hoặc aiohttp cho các client Gemini/OpenAI (hoặc sử dụng wrapper bất đồng bộ tương ứng).
2. **Service Layer (Nghiệp vụ Prompt)**:
   - Tạo thư mục `services/` và file `services/prompt_service.py`.
   - Di chuyển khối logic xử lý prompt (generate_prompts) từ `ai_prompts.py` sang file này và biến nó thành một hàm `async`.
3. **Re-export (`ai_prompts.py`)**:
   - `ai_prompts.generate_prompts()` cũ sẽ trở thành hàm bọc: gọi `asyncio.run(prompt_service.generate_prompts(...))` để giữ tương thích ngược với code đồng bộ cũ.

## CÁC FILE CẦN CAN THIỆP
- Thư mục mới: `services/`
- Thêm file: `infrastructure/ai_pool.py`, `services/prompt_service.py`
- Sửa đổi: `ai_prompts.py`
