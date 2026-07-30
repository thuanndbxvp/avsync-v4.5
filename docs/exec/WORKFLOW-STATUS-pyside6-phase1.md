# WORKFLOW STATUS — pyside6-phase1

> Theo skill `.ai-pipeline/skills/code.md`, Mục "8-STEP EXECUTION LOOP".
> Mỗi step được đánh dấu `[x] done` sau khi CODING + POST-CHECK xong.

| Step | Tên | File(s) | Lines | Trạng thái |
|------|-----|---------|-------|-----------|
| 1 | Cập nhật requirements.txt (thêm PySide6 + sửa comment đầu file) | `requirements.txt` | 23 dòng | [x] done |
| 2 | Đổi tên file cũ | `app.py` → `app_legacy.py` (git mv) | 0 | [x] done |
| 2.5 | Cập nhật `preflight.py` (tách 2 sub-check) | `preflight.py` | 6 dòng thay đổi | [x] done |
| 2.6 | Cập nhật `build_release.bat` (Nuitka target PySide6) | `build_release.bat` | 2 token thay đổi | [x] done |
| 3 | Tạo cấu trúc thư mục UI | `ui/__init__.py`, `ui/tabs/__init__.py` | +2 | [x] done |
| 4 | Tạo CSS (QSS) | `ui/style.qss` | +mới | [x] done |
| 5 | Khung MainWindow | `ui/main_window.py` | +mới | [x] done |
| 6 | Entry point mới | `app.py` (mới) | +mới | [x] done |
| 7 | Kiểm định (Audit) | n/a | n/a | [x] done |

## Lệnh kiểm tra sau mỗi step
- Compile: `python -m py_compile <file>`
- Smoke GUI: `python app.py` (Bước 7)
- Linter: `python -m pyflakes <file>` (nếu cài)
- CodeGraph: `codegraph index` rồi `codegraph_impact`

## Tổng kết Phase 1
- Tổng file mới: 4 (`app.py` mới, `ui/__init__.py`, `ui/style.qss`, `ui/main_window.py`)
- Tổng file đổi tên: 1 (`app.py` → `app_legacy.py`)
- Tổng file sửa: 3 (`requirements.txt`, `preflight.py`, `build_release.bat`)
