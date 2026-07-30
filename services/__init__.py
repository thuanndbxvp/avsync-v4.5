"""Service layer — use case orchestration (mix domain + infrastructure).

Mỗi service đại diện cho 1 USE CASE nghiệp vụ (generate_prompts, render_video,
queue_manager, ...) chứ không phải 1 file thuần I/O hay pure logic.
Service được phép import cả domain (pure) + infrastructure (I/O).
"""