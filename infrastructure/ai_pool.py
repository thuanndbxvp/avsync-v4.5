"""infrastructure.ai_pool — Async Pool cho network I/O (AI API calls).

Dùng `asyncio.Semaphore` để giới hạn concurrency (tránh 429 rate limit)
và `asyncio.gather` để chạy N request SONG SONG (mỗi cái là 1 task).
Mỗi call API blocking (urllib) được bọc trong `asyncio.to_thread()` — đây là
cách duy nhất để có async concurrency THẬT mà KHÔNG cần thư viện bên ngoài
(aiohttp/httpx). Zero new dependency.

Kỳ vọng khi AI provider trả lời lần đầu ~5s:
  - Sequential (cũ):  N batch * 5s = N*5s
  - Parallel (mới):  ceil(N / max_concurrent) * 5s   → có thể nhanh gấp 5-10 lần
"""
from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Iterable


class AsyncAIPool:
    """Async pool giới hạn số request đồng thời (semaphore).

    Dùng cho mọi AI call để:
      - Chạy song song (gather) -> tăng throughput
      - Giới hạn concurrency (semaphore) -> tránh rate limit 429
      - Giữ thứ tự input/output (gather default)
    """

    def __init__(self, max_concurrent: int = 5):
        self._max = max(1, int(max_concurrent))
        self._sem = asyncio.Semaphore(self._max)
        self._stats = {"started": 0, "finished": 0, "errors": 0, "in_flight": 0}

    @property
    def max_concurrent(self) -> int:
        return self._max

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    async def gather(self, tasks: Iterable[Awaitable]) -> list:
        """Run many awaitables with bounded concurrency. Trả list kết quả.

        Mỗi task được bọc trong semaphore — số task chạy cùng lúc ≤ max_concurrent.
        Kết quả giữ thứ tự (gather, không phải as_completed).
        Lỗi của 1 task KHÔNG hủy các task khác (return_exceptions=True).
        """
        tasks = list(tasks)
        if not tasks:
            return []

        async def _run(idx: int, co: Awaitable):
            async with self._sem:
                self._stats["in_flight"] += 1
                self._stats["started"] += 1
                try:
                    r = await co
                    return idx, r
                except Exception as e:
                    self._stats["errors"] += 1
                    return idx, e
                finally:
                    self._stats["in_flight"] -= 1
                    self._stats["finished"] += 1

        wrapped = [_run(i, t) for i, t in enumerate(tasks)]
        # gather keeps ordering even if return_exceptions=True (we already catch)
        results = await asyncio.gather(*wrapped)
        # results is list[tuple[int, result/error]] — sort by idx to keep input order
        results.sort(key=lambda r: r[0])
        return [r[1] for r in results]

    def gather_sync(self, tasks: Iterable[Awaitable]) -> list:
        """Sync entry point: tạo pool, chạy gather, đợi xong. Dùng từ code sync.

        Tương thích ngược với code sync gọi `_run_batches`. Trả list cùng thứ tự input.
        Task đầu vào MỖI CÁI đã là awaitable (do caller tạo bằng `to_thread`).
        """
        return asyncio.run(self.gather(tasks))

    # ----------------- helpers -----------------
    @staticmethod
    def to_thread_sync(fn, *args, **kwargs) -> Awaitable:
        """Bọc 1 hàm sync (vd `_call(provider, key, model, system, user)`) thành awaitable.

        Mỗi call API blocking sẽ chạy trên thread riêng (default executor) -> không
        block event loop; kết hợp với semaphore ở gather() để giới hạn song song.
        """
        return asyncio.to_thread(fn, *args, **kwargs)


# ----------------- AsyncBatcher helper -----------------
async def run_batches_async(
    pool: AsyncAIPool,
    call_fn: Callable[..., Awaitable],
    items: list,
    *, batch_size: int, **call_kwargs,
) -> list:
    """Chạy 1 batch async: chia `items` thành những batch nhỏ (batch_size), mỗi batch
    được dispatch SONG SONG (với max_concurrent từ pool). Trả list cùng thứ tự.

    Khác với logic cũ (sequential batches), tool thường bó 1 lần toàn bộ items
    vào 1 batch_size lớn -> concurrency cao nhất = max_concurrent.

    call_fn(batch, **kwargs) -> Awaitable[list[str]]   (1 call AI trả list prompt cho batch đó)
    """
    if not items:
        return []
    out: list = [None] * len(items)
    n = len(items)
    pos = 0
    while pos < n:
        chunk = items[pos:pos + batch_size]
        async def _one(chunk=chunk, start=pos):
            r = await call_fn(chunk, **call_kwargs)
            # r: list[str] độ dài = len(chunk)
            if not isinstance(r, list):
                raise RuntimeError(f"call_fn phải trả list[str]; nhận {type(r).__name__}")
            return start, r
        results = await pool.gather([_one()])
        for start, r in results:
            for i, v in enumerate(r):
                if start + i < n:
                    out[start + i] = v
        pos += batch_size
    return out
