"""Smoke test Milestone 2: AsyncAIPool + services.prompt_service + backward-compat."""
import asyncio
import sys
import time

sys.path.insert(0, r"d:\auto-edit-video-main")

# ---------- Test 1: AsyncAIPool imports ----------
from infrastructure.ai_pool import AsyncAIPool, run_batches_async
print("[OK] AsyncAIPool + run_batches_async imports")

# ---------- Test 2: AsyncAIPool.gather với concurrency thật ----------
# 5 task, mỗi task sleep 0.5s. Nếu chạy sequential -> ~2.5s. Nếu song song (max_concurrent=5) -> ~0.5s.
async def slow_task(t):
    await asyncio.sleep(0.5)
    return f"done-{t}"

async def main_test():
    pool = AsyncAIPool(max_concurrent=5)
    t0 = time.monotonic()
    results = await pool.gather([slow_task(i) for i in range(5)])
    elapsed = time.monotonic() - t0
    assert results == [f"done-{i}" for i in range(5)], f"Order broken: {results}"
    assert elapsed < 1.0, f"Should run in ~0.5s (5 concurrent), took {elapsed:.2f}s"
    print(f"[OK] AsyncAIPool.gather parallel (5 tasks in {elapsed:.2f}s vs sequential ~2.5s)")
    return elapsed

elapsed_parallel = asyncio.run(main_test())

# ---------- Test 3: AsyncAIPool giới hạn concurrency ----------
# 8 task, mỗi task sleep 0.3s. max_concurrent=3 -> 3 batch x 0.3s ≈ 0.9s
async def slow_task_counted(idx, counter):
    async with counter["pool_lock"]:
        counter["now"] += 1
        counter["peak"] = max(counter["peak"], counter["now"])
    await asyncio.sleep(0.3)
    async with counter["pool_lock"]:
        counter["now"] -= 1
        counter["done"] += 1
    return f"task-{idx}"

async def main_test_limit():
    counter = {"now": 0, "peak": 0, "done": 0, "pool_lock": asyncio.Lock()}
    pool = AsyncAIPool(max_concurrent=3)
    t0 = time.monotonic()
    # need to wrap the counter into task
    async def wrapped(idx):
        return await slow_task_counted(idx, counter)
    results = await pool.gather([wrapped(i) for i in range(8)])
    elapsed = time.monotonic() - t0
    # 8 task / 3 max → ceil(8/3) = 3 batch x 0.3s = ~0.9s
    assert 0.85 <= elapsed <= 1.5, f"Expected ~0.9s (3 concurrent x 0.3s), got {elapsed:.2f}s"
    assert counter["peak"] <= 3, f"Concurrency exceeded: peak={counter['peak']}"
    assert counter["peak"] >= 2, f"Should reach at least 2 concurrent, peak={counter['peak']}"
    assert counter["done"] == 8
    print(f"[OK] AsyncAIPool semaphore limits concurrency (peak={counter['peak']}, "
          f"8 tasks in {elapsed:.2f}s vs sequential ~2.4s)")
    return elapsed

elapsed_limited = asyncio.run(main_test_limit())

# ---------- Test 4: gather giữ thứ tự input/output ----------
async def main_test_order():
    pool = AsyncAIPool(max_concurrent=3)
    async def var(i):
        # reverse latency theo index để đảm bảo gather không sort theo finish time
        await asyncio.sleep(0.01 * (5 - i))
        return i * 10
    results = await pool.gather([var(i) for i in range(5)])
    assert results == [0, 10, 20, 30, 40], f"Order not preserved: {results}"
    print("[OK] AsyncAIPool.gather preserves input order")

asyncio.run(main_test_order())

# ---------- Test 5: gather với task raises — không hủy các task khác ----------
async def main_test_errors():
    pool = AsyncAIPool(max_concurrent=2)
    async def ok(i):
        await asyncio.sleep(0.05)
        return i
    async def bad():
        await asyncio.sleep(0.05)
        raise ValueError("boom")
    results = await pool.gather([ok(1), bad(), ok(2), bad(), ok(3)])
    assert results[0] == 1
    assert isinstance(results[1], ValueError)
    assert results[2] == 2
    assert isinstance(results[3], ValueError)
    assert results[4] == 3
    print("[OK] AsyncAIPool.gather isolates errors (does not cancel siblings)")

asyncio.run(main_test_errors())

# ---------- Test 6: to_thread_sync (wraps sync fn as awaitable) ----------
async def main_test_thread():
    pool = AsyncAIPool(max_concurrent=4)
    def sync_mul(x, y):
        time.sleep(0.1)   # blocking I/O
        return x * y
    t0 = time.monotonic()
    calls = [pool.to_thread_sync(sync_mul, i, 10) for i in range(8)]
    results = await pool.gather(calls)
    elapsed = time.monotonic() - t0
    assert results == [0, 10, 20, 30, 40, 50, 60, 70], results
    # 8 tasks / 4 max_concurrent -> 2 batches x 0.1s = ~0.2s
    assert 0.18 <= elapsed <= 0.6, f"Expected ~0.2s, got {elapsed:.2f}s"
    print(f"[OK] to_thread_sync + pool: 8 blocking tasks in {elapsed:.2f}s vs sequential ~0.8s")

asyncio.run(main_test_thread())

# ---------- Test 7: backward-compat — code sync import ai_prompts không đổi ----------
import ai_prompts as ap
import services.prompt_service as svc
assert callable(ap.generate_prompts)
assert callable(ap.generate_motion_prompts)
assert callable(ap.generate_chain_prompts)
assert callable(ap.qc_scene_match)
assert callable(svc.generate_prompts_async)
assert callable(svc.generate_motion_prompts_async)
print("[OK] backward-compat: ai_prompts.{generate,motion,chain,qc} + async_* all callable")

# ---------- Test 8: API key validation (sync shim) ----------
try:
    ap.generate_prompts(["test"], "{}", "")
    raise AssertionError("Should raise RuntimeError")
except RuntimeError as e:
    assert "API key" in str(e), str(e)
print("[OK] generate_prompts sync shim raises on empty API key")

try:
    ap.generate_prompts(["test"], "", "fake-key")
    raise AssertionError("Should raise RuntimeError (style empty)")
except RuntimeError as e:
    assert "Style" in str(e) or "API" in str(e), str(e)
print("[OK] generate_prompts sync shim raises on empty style (in_prompt mode)")

# ---------- Test 9: API key validation (async) ----------
try:
    asyncio.run(svc.generate_prompts_async(["test"], "{}", ""))
    raise AssertionError("Should raise RuntimeError")
except RuntimeError as e:
    assert "API key" in str(e), str(e)
print("[OK] generate_prompts_async raises on empty API key")

# ---------- Test 10: workers + UI still import ----------
import importlib
for mod in [
    "core.worker_prompt", "core.worker_render", "core.worker_sleep",
    "core.worker_queue", "ui.main_window", "ui.tabs.tab_prompt",
]:
    importlib.import_module(mod)
print("[OK] core/worker_* + ui/main_window + ui/tabs/tab_prompt all import")

# ---------- Test 11: async shim raise on generate_chain_prompts ----------
# Có scenes_text nhưng API key rỗng -> phải raise.
try:
    ap.generate_chain_prompts(["scene 1"], "{}", "")
    raise AssertionError("Should raise")
except RuntimeError as e:
    assert "API key" in str(e), str(e)
print("[OK] generate_chain_prompts sync shim raises on empty API key")

# Empty scenes_text với key thật: trả ([], []) — không raise
res = ap.generate_chain_prompts([], "{}", "fake-key")
assert res == ([], []), f"Empty should return ([], []), got {res}"
print("[OK] generate_chain_prompts returns ([], []) for empty scenes")

# ---------- Test 12: M1 + M1.5 backward-compat kiểm tra nhanh ----------
from domain.timeline import _ends_with_punctuation, parse_srt, group_scenes
import auto_edit as ae
assert callable(ae.parse_srt)
assert callable(ae._ass_time)
assert _ends_with_punctuation("Hi.") is True
segs = parse_srt(r"d:\auto-edit-video-input\test_milestone1.srt")
scenes = group_scenes(segs, 8.0)
assert len(scenes) >= 1
print("[OK] M1 + M1.5 backward-compat (parse_srt, group_scenes, _ends_with_punct)")

print("\n=== ALL MILESTONE 2 TESTS PASSED ===")