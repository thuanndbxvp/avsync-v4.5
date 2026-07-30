# MICRO-STEP EXECUTION WORKFLOW: REFACTOR MILESTONE 3

Tuân thủ nghiêm ngặt các bước dưới đây để tối ưu hóa Pipeline FFMPEG.

## BƯỚC 1: Xây dựng FFMPEG Client
1. Mở file `infrastructure/ffmpeg_client.py`.
2. Tạo hàm `build_master_clip(scenes_list, output_path)`. Thay vì chạy vòng lặp gọi lệnh FFMPEG cho từng ảnh, hãy sinh ra 1 câu lệnh FFMPEG khổng lồ chứa nhiều `-i` và chuỗi `-filter_complex` để nối các ảnh này lại với nhau (hoặc xfade).

## BƯỚC 2: Xây dựng Render Service
1. Tạo file `services/render_service.py`.
2. Viết hàm `render_video(srt_path, img_dir, out_path, cfg, progress_cb)`.
3. Hàm này sẽ lấy logic lập kế hoạch (Plan) từ `domain/render_plan.py` (đã tách ở M1), sau đó thảy danh sách cảnh vào `ffmpeg_client.build_master_clip` để xuất ra file cuối.

## BƯỚC 3: Thay ruột God Function
1. Mở `auto_edit.py`, tìm đến hàm `render_video()`.
2. Xóa hàng trăm dòng code lộn xộn trong đó.
3. Chèn vào lời gọi:
```python
def render_video(srt, img_dir, out, cfg=None, progress_cb=None):
    from services.render_service import render_video as rv
    return rv(srt, img_dir, out, cfg, progress_cb)
```

## BƯỚC 4: Kiểm định (Audit)
- Chạy lệnh CLI cũ để render một video 10 cảnh.
- Thời gian render phải giảm đáng kể so với trước. Check MD5 hash hoặc xem video đầu ra để đảm bảo chất lượng hình/tiếng không đổi (Zero Regression).
