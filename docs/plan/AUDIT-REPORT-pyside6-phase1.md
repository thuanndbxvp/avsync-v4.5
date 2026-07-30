# AUDIT REPORT — pyside6-phase1

> **Tác giả:** Tầng 2 (Kỹ sư Thực thi)
> **Ngày:** 2026-07-30
> **Trạng thái:** ❌ **CHƯA CODE — CHỜ TẦNG 1 PHÊ DUYỆT**
> **Tuân thủ:** TIER2_PROMPT.md, Mục 1 — Quyền PRE-AUDIT, Mục 4 — Luật thoát hiểm

---

## 0. Tóm tắt 1 dòng

MSEW-thiết-kế-thiếu-bước: Bước 2 "đổi tên `app.py` → `app_legacy.py`" làm **`preflight.py`, `app.py mới`, `run.bat`, `build_release.bat` đứt mạch** trước khi kịp đến Phase tiếp theo. Tôi đề xuất Tầng 1 chốt lại "cầu nối" rồi tôi mới gõ code.

---

## 1. Phát hiện nghiêm trọng — phá vỡ runtime ngay khi Bước 2 chạy

### 1.1. `preflight.py:79` import từ module tên `app` (đúng tên file cũ)

```22:preflight.py
import app  # noqa  (sau khi compile OK)
```

```101:preflight.py
    a = app.App(r)
```

- `preflight.py` được `build_release.bat` gọi làm bước `[0/2]` bắt buộc trước khi Nuitka đóng gói.
- Ngay khi tôi `git mv app.py app_legacy.py` theo Bước 2 → `import app` sẽ ném **`ModuleNotFoundError: No module named 'app'`**.
- Mọi lần `python preflight.py` từ bây giờ fail, kéo theo `build_release.bat` không thể ra bản release (dòng 18-19).

### 1.2. `run.bat:10/14/18` cứng nhắc gọi `%~dp0app.py`

```10:run.bat
  start "" pyw "%~dp0app.py"
```

```14:run.bat
  start "" pythonw "%~dp0app.py"
```

```18:run.bat
  start "" "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" "%~dp0app.py"
```

- Ba nhánh fallback trong `run.bat` đều `start "" … app.py`. Sau khi Bước 2 đổi tên, user double-click `run.bat` → Windows báo lỗi "không tìm thấy file".
- MSEW Bước 6 sẽ tạo `app.py` mới (PySide6), nhưng đó là **entry point khác** — user chưa quen với việc phải gõ `python app.py`. Tầng 1 cần quyết định: có giữ `run.bat` là "vỏ" chạy cả `app_legacy.py` (dev muốn rollback) lẫn `app.py` mới không?

### 1.3. `build_release.bat:29` Nuitka target là `app.py` (cũ)

```29:build_release.bat
python -m nuitka --standalone --onefile --enable-plugin=tk-inter … --output-filename=AutoEditVideo.exe app.py
```

- Lệnh Nuitka hiện đóng gói file `app.py` cũ + bật plugin `tk-inter`. Sau Phase 1, `app.py` mới là PySide6 — `--enable-plugin=tk-inter` sẽ thành **dead-weight** và thiếu `--enable-plugin=pyside6`. Nuitka sẽ compile được nhưng output .exe dùng Tkinter cũ.
- Tầng 1 cần quyết: **(a) giữ build_release.bat đóng gói `app_legacy.py`** (giữ kênh rollback cho khách cũ) hay **(b) chuyển sang đóng gói `app.py` mới** (PySide6, cần update plugin Nuitka).

### 1.4. `preflight.py` còn tham chiếu cấu trúc cũ

- `FILES = ["app.py", "auto_edit.py", ...]` ở `preflight.py:30-31` — đang compile `app.py` để bắt SyntaxError. Sau khi đổi tên, `preflight.py` vẫn compile `app.py` mới (PySide6) — có thể không lỗi, nhưng AST-scan trùng tên hàm của `app.py` mới (5 dòng) sẽ vô nghĩa.
- Bước 3 của `preflight.py` đọc `open("app.py")` và `import app` → đọc logic cũ. Nếu `app.py` mới chỉ import `QApplication`, các check `default_config()` / `App` sẽ nổ.

---

## 2. Phát hiện phụ — phá vỡ / mâu thuẫn tiềm ẩn

### 2.1. `requirements.txt` mâu thuẫn nội tại với Bước 1 MSEW

- Comment đầu file (dòng 2-4) tuyên bố: *"Tool hiện CHỈ dùng thư viện chuẩn của Python 3 + FFmpeg. Không cần cài package pip nào để chạy phần render video."*
- Bước 1 MSEW: *"Thêm `PySide6` vào cuối file `requirements.txt`"*.
- Tôi đề xuất khi thêm PySide6, đồng thời **cập nhật comment đầu file** để khỏi tự mâu thuẫn (xếp vào "fix code smell", không phải scope creep).

### 2.2. `install.bat:58` chạy `pip install -r requirements.txt`

- Sau khi requirements.txt có PySide6, `install.bat` (mà user chạy khi cài mới Windows) sẽ tự cài PySide6 ≈ 200MB. OK, nhưng cần chú ý **tăng đáng kể thời gian cài đặt**. Tầng 1 có muốn tách PySide6 thành requirement tùy chọn (ghi chú: GUI mới) không?

### 2.3. `venv/` đã có trong repo nhưng `install.bat` KHÔNG dùng venv

```1:install.bat
python -m pip install -r requirements.txt --quiet
```

- Cài vào global env, không vào `venv/`. MSEW nói *"Cài đặt vào môi trường `venv` nếu cần thiết"* → Tầng 1 chưa rõ "cần" là lúc nào. Nếu user đã có package cũ khác version trong global Python → PySide6 mới **xung đột tiềm ẩn**.

---

## 3. Kiểm tra crash runtime / thư viện mới — theo Mục 1 TIER2_PROMPT

- **PySide6** mới hoàn toàn (chưa có trong requirements.txt hiện tại) → đúng nghĩa "thư viện mới cần cài đặt".
- PLAN-PHASE1 không nói cài pip — MSEW để dấu nhắc "*(Cài đặt vào môi trường `venv` nếu cần thiết)*".
- Tôi **CẢNH BÁO**: nếu sếp không pip install PySide6 trước, thì Bước 7 (chạy `python app.py`) sẽ ném `ModuleNotFoundError: No module named 'PySide6'` ngay dòng `from PySide6.QtWidgets import …`.

---

## 4. Đề xuất bổ sung 2 bước cho MSEW — chờ Tầng 1 chốt

> Hai bước dưới đây **không có trong MSEW-gốc**, tôi **KHÔNG tự ý thêm**. Đây là đề xuất để Tầng 1 cập nhật `MSEW-pyside6-phase1.md` rồi tôi mới triển khai.

### Bước 2.5 (đề xuất): Cập nhật `preflight.py` để không đứt mạch

- Đổi `FILES = [...]` thành `FILES = ["app_legacy.py", "app.py", ...]`
- Bước 3 (compile `app.py` + `import app`) phải biết `app.py` mới chỉ là stub PySide6 (không có `default_config`, không có `App` class), nên **cần tách thành 2 sub-section**: một check compile/import cho `app_legacy.py` (giữ logic cũ), một check smoke cho `app.py` mới (chỉ cần import `QApplication` không crash).

### Bước 2.6 (đề xuất): Cập nhật `run.bat` để chuyển hướng entry point

- 3 nhánh `start "" … app.py` → đổi thành `app.py` mới (PySide6 — entry point Phase 1 là PySide6).
- Tầng 1 nên quyết: có **giữ fallback `app_legacy.py`** (user gõ `python app_legacy.py` để chạy GUI tkinter cũ trong lúc dev Phase 2) không?

### Bước 2.7 (đề xuất): Cập nhật `build_release.bat`

- Sau Phase 1, Nuitka target nên là `app.py` mới (PySide6).
- Đổi `--enable-plugin=tk-inter` → `--enable-plugin=pyside6`.
- Thêm `--include-package=PySide6` (Nuitka onefile có khi cần) để khỏi mất DLL khi chạy trên máy không cài PySide6.

---

## 5. Kết luận & câu hỏi cho Tầng 1

**Tôi CHƯA gõ bất kỳ dòng code nào**, đúng luật Tiền-Kiểm Mục 1 TIER2_PROMPT.

Sếp vui lòng trả lời (chọn nhiều nếu muốn):

**Câu hỏi Q1:** Về `run.bat` — nên đổi thẳng sang gọi `app.py` mới (PySide6), hay **giữ fallback** cho `app_legacy.py`?

**Câu hỏi Q2:** Về `preflight.py` — Tầng 1 muốn tôi **tự tách thành 2 sub-check** (legacy + mới), hay **tạm thời loại `app.py` mới khỏi FILES** để chỉ check `app_legacy.py` cho đến khi Phase 2 có logic thật?

**Câu hỏi Q3:** Về `build_release.bat` — sau Phase 1, build target nên là `app.py` PySide6 (kèm update plugin Nuitka sang `pyside6`), hay **trì hoãn** (vẫn build `app_legacy.py` để khách cũ tiếp tục dùng được)?

**Câu hỏi Q4:** Về `install.bat` — `pip install -r requirements.txt` đang cài vào global. Tầng 1 muốn giữ nguyên (đơn giản), hay **tách PySide6 thành requirement tùy chọn** (user phải bỏ comment mới cài GUI mới)?

**Câu hỏi Q5:** Sau khi sếp trả lời Q1-Q4, tôi sẽ:
- Cập nhật `MSEW-pyside6-phase1.md` theo câu trả lời? — hay **Tầng 1 tự cập nhật** để giữ split-of-concern?

---

## 6. Trạng thái hiện tại của repo

| File | Trạng thái | Ghi chú |
|------|-----------|---------|
| `app.py` (137KB, 2516+ dòng) | chưa đổi | tkinter, có `App` class (dòng 2553), `default_config()` |
| `requirements.txt` | chưa đổi | có `requests`, `cryptography` — chưa có PySide6 |
| `ui/` | chưa tồn tại | |
| `ui/tabs/` | chưa tồn tại | |
| `ui/style.qss` | chưa tồn tại | |
| `ui/main_window.py` | chưa tồn tại | |
| `preflight.py` | sẽ lỗi ngay khi Bước 2 chạy | `import app` |
| `run.bat` | sẽ lỗi "file not found" | hard-code `app.py` |
| `build_release.bat` | sẽ build nhầm plugin | `--enable-plugin=tk-inter` |
| `install.bat` | OK (cài global) | sẽ thêm 200MB PySide6 |

Chờ sếp phản hồi trước khi vào `WORKFLOW-STATUS-pyside6-phase1.md` và gõ code.
