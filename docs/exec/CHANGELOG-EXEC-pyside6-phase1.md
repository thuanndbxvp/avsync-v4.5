# CHANGELOG EXEC — pyside6-phase1

> Theo skill `.ai-pipeline/skills/code.md`. Ghi lại file nào đã sửa, bao nhiêu dòng, trạng thái.

| Step | File | Lines Changed | Status |
|------|------|---------------|--------|
| 1 | `requirements.txt` | 23 dòng (sửa comment + thêm PySide6 cuối file) | DONE |
| 2 | `app.py` → `app_legacy.py` | rename (git mv, status `R`) — không sửa nội dung | DONE |
| 2.5 | `preflight.py` | 6 dòng đổi tên `app` → `app_legacy` (FILES, import, App(), _config_path, load_config, AST check) + thêm `_compile_only` helper cho stub `app.py` | DONE |
| 2.6 | `build_release.bat` | 2 flag Nuitka: `--enable-plugin=tk-inter` → `--enable-plugin=pyside6 --include-package=PySide6` | DONE |
| 3 | `ui/__init__.py`, `ui/tabs/__init__.py` | 2 file rỗng | DONE |
| 4 | `ui/style.qss` | mới (Streamline Logic) | DONE |
| 5 | `ui/main_window.py` | mới (113 dòng, copy từ MSEW verbatim) | DONE |
| 6 | `app.py` (mới) | mới (29 dòng, entry point PySide6) | DONE |
| 7 | Kiểm định | py_compile PASS (11/11), import chain PASS, GUI smoke PASS (process sống >4s), preflight PASS cho mọi check liên quan Phase 1 | DONE |
