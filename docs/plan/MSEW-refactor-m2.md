# MICRO-STEP EXECUTION WORKFLOW: REFACTOR MILESTONE 2

Tuân thủ nghiêm ngặt các bước dưới đây để tối ưu hóa AI Generation bằng AsyncIO. Đảm bảo Zero Regression.

## BƯỚC 1: Xây dựng AI Pool (Infrastructure)
1. Tạo file `infrastructure/ai_pool.py`.
2. Viết class `AsyncAIPool` với phương thức `async def gather_prompts(self, tasks, max_concurrent=5)`.
3. Bên trong phương thức, sử dụng `asyncio.Semaphore(max_concurrent)` và `asyncio.gather(*tasks)` để chạy song song các Request AI.

## BƯỚC 2: Bóc tách Prompt Service
1. Tạo thư mục `services/` và file `services/prompt_service.py`.
2. Chuyển hàm `generate_prompts` và `_run_batches` (hoặc logic tương đương) từ `ai_prompts.py` sang đây.
3. Chuyển đổi các hàm này thành hàm `async` (`async def`). Lợi dụng `AsyncAIPool` vừa tạo ở Bước 1 để dispatch API calls.

## BƯỚC 3: Re-export & Tương thích ngược
1. Mở file `ai_prompts.py` cũ.
2. Xóa ruột hàm `generate_prompts` cũ đi, thay thế bằng:
```python
def generate_prompts(texts, style, key, model=None, ...):
    from services.prompt_service import generate_prompts_async
    import asyncio
    # Bọc hàm async thành đồng bộ cho UI cũ gọi
    return asyncio.run(generate_prompts_async(texts, style, key, model, ...))
```
*(Nếu Worker của UI đã chuyển sang hỗ trợ async ở Phase trước, có thể gọi thẳng async).*

## BƯỚC 4: Kiểm định (Audit)
- Mở Tab Tạo Prompt trên giao diện PySide6, nhập thông số và bấm chạy.
- Quan sát tốc độ trả về. Nếu tốc độ cải thiện rõ rệt và không có lỗi Crash, Milestone 2 thành công!
