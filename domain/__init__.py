"""Domain layer — pure business logic, NO I/O.

Quy tắc cứng:
  - KHÔNG import os, subprocess, request, httpx, urllib, asyncio.
  - Chỉ chứa hàm tính toán thuần (parse, format, transform, validate).
  - Phụ thuộc domain -> stdlib ONLY.

Mọi thứ liên quan đến file, subprocess, network đều thuộc `infrastructure/`.
"""