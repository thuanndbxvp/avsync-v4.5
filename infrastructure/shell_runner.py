"""infrastructure.shell_runner — bọc subprocess.run() với log + timeout chuẩn.

Mục tiêu:
  - Một điểm duy nhất gọi subprocess — sau này dễ thêm streaming log, async,
    hoặc retry mà không phải sửa 30 chỗ trong code.
  - Hiện tại giữ API sync (compat với code cũ); Phase C sẽ thêm async variant.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from typing import Callable, Optional, Sequence


def run_cmd(
    args: Sequence[str],
    *,
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    log: Optional[Callable[[str], None]] = None,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """Chạy 1 lệnh, log ra UI nếu có.

    args   : list argv (KHÔNG truyền string -> tránh shell injection).
    timeout: giây; None = đợi vô hạn.
    log    : callback nhận từng dòng stderr (nếu capture=True).
    capture: True = chụp stdout/stderr; False = để inherit (in ra console).
    """
    if log and capture:
        proc = subprocess.Popen(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
       )
        # đọc song song; log cả 2 stream ra callback
        import threading

        def _pump(stream, prefix=""):
            for line in stream:
                if line:
                    log(f"{prefix}{line.rstrip()}")

        t_out = threading.Thread(target=_pump, args=(proc.stdout, ""), daemon=True)
        t_err = threading.Thread(target=_pump, args=(proc.stderr, ""), daemon=True)
        t_out.start(); t_err.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise
        t_out.join(); t_err.join()
        return subprocess.CompletedProcess(
            args=args, returncode=proc.returncode,
            stdout="", stderr="",
        )

    return subprocess.run(
        list(args),
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=cwd,
        check=False,
    )


def quote_for_log(args: Sequence[str]) -> str:
    """Log lại lệnh shell (để debug) — quote đúng để không bị confuse bởi space."""
    if sys.platform == "win32":
        return subprocess.list2cmdline(list(args))
    return " ".join(shlex.quote(a) for a in args)