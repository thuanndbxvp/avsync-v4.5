"""services.render_service — orchestration cho use case 'render video'.

Move logic từ `auto_edit.render_video()` (400 dòng God Function) sang đây.
Tách thành 3 giai đoạn (Plan -> Gather Clips -> Master Concat + Final):
  1. PLAN       — domain.render_plan (pure: scenes, total_end, fps, encoder, jobs)
  2. GATHER     — render per-scene song song (ThreadPoolExecutor, builds/clip_N.mp4)
  3. CONCAT     — concat hoặc xfade (infrastructure.ffmpeg_client.concat_or_xfade)
  4. FINALIZE   — color + sub + voice + bgm + logo (ffmpeg_client.compose_final)

STRANGLER: `auto_edit.render_video(...)` cũ giờ là 1 shim 6 dòng gọi
`services.render_service.render_video(...)`. Public signature Y CHANG.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
import types
from concurrent.futures import ThreadPoolExecutor

from domain.render_plan import (
    ScenePlan, RenderPlan, plan_scenes, choose_fps, choose_encoder_jobs,
    apply_max_scenes, derive_total_end, normalize_aspect,
    DEFAULT_IMAGE_EXTS, DEFAULT_VIDEO_EXTS,
)
from infrastructure import ffmpeg_client
from infrastructure.shell_runner import run_cmd


# Sentinel: dùng internal helpers từ auto_edit (single source of truth cho render stage).
def _ae():
    """Lazy import auto_edit."""
    import auto_edit as ae
    return ae


def render_video(srt_path: str, img_dir: str, out_path: str,
                 cfg: dict | None = None, progress_cb=None) -> bool:
    """Render từ SRT + ảnh/clip -> MP4. Public signature giống auto_edit.

    args = {srt_path, img_dir, out_path, cfg={}, progress_cb=callable}
    Returns True on success.
    """
    cfg = cfg or {}
    ae = _ae()

    args = _build_args(srt_path, img_dir, out_path, cfg)

    def log(msg):
        if progress_cb:
            progress_cb(msg)

    if not ae.FFMPEG:
        raise SystemExit("Không tìm thấy ffmpeg. Hãy cài rồi thử lại.")
    if not os.path.isfile(args.srt):
        raise SystemExit(f"Không thấy file SRT: {args.srt}")

    # 9:16 vertical -> update globals + log
    width, height = normalize_aspect(args.aspect)
    if args.aspect == "9:16":
        ae.WIDTH, ae.HEIGHT = 1080, 1920
        log("• Khung hình: 9:16 DỌC (1080x1920 — Shorts/TikTok/Reels)")

    # ----------- STAGE 1. PLAN (pure) -----------
    segs = ae.parse_srt(args.srt)
    if not segs:
        raise SystemExit("File SRT không có đoạn nào hợp lệ.")
    media = ae.collect_media(args.images)
    if not media:
        raise SystemExit(f"Thư mục {args.images} chưa có ảnh/video nào.")
    voice = ae.find_voice(args.input_dir, args.voice)
    audio_dur = ae.probe_duration(voice) if voice else None
    total_end = derive_total_end(segs, audio_dur)

    scenes_pl, mode_label = plan_scenes(
        segs=segs, media=media, total_end=total_end,
        mode=args.image_mode, seconds_per_image=args.seconds_per_image,
        scenes_csv=args.scenes, n_img=len(media), n_seg=len(segs),
    )
    scenes_pl, total_end, extra_label = apply_max_scenes(
        scenes_pl, args.max_scenes, total_end,
    )
    mode_label = f"{mode_label} | {extra_label}" if extra_label else mode_label

    log(f"• {len(segs)} đoạn phụ đề | {len(media)} ảnh/clip | "
        f"{os.path.basename(voice) if voice else 'KHÔNG có voice'}")
    log(f"• Rải ảnh: {mode_label} → {len(scenes_pl)} cảnh | tổng video {total_end:.1f}s")

    # Dry-run path
    if args.dry_run:
        for i, sp in enumerate(scenes_pl):
            log(f"   cảnh {i+1:>3}: {os.path.basename(sp.source):<22} {sp.duration:6.2f}s")
        log(f"   → TỔNG {sum(s.duration for s in scenes_pl):.1f}s "
            f"(khớp voice/SRT {total_end:.1f}s)")
        return True

    # ----------- STAGE 2. GATHER CLIPS (parallel) -----------
    tmp = tempfile.mkdtemp(prefix="autoedit_")
    try:
        # Fix broken 1-frame clips: replace with first frame PNG
        for i, sp in enumerate(scenes_pl):
            if sp.source.lower().endswith(DEFAULT_VIDEO_EXTS):
                dur = ae.probe_duration(sp.source)
                if not dur or dur < 0.2:
                    png = os.path.join(tmp, f"fix_{i:04d}.png")
                    try:
                        run_cmd([ae.FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                                 "-i", sp.source, "-frames:v", "1", png], timeout=120)
                        if os.path.isfile(png):
                            scenes_pl[i] = ScenePlan(source=png, duration=sp.duration)
                            log(f"  ⚠️ Clip hỏng (1 frame): {os.path.basename(sp.source)} "
                                f"— đã dùng như ẢNH TĨNH (Ken Burns) thay thế")
                    except SystemExit:
                        pass

        # Choose FPS
        probed_fps = {}
        for sp in scenes_pl:
            if sp.source.lower().endswith(DEFAULT_VIDEO_EXTS):
                f = ae.probe_fps(sp.source)
                if f:
                    probed_fps[sp.source] = f
        fps, fps_why = choose_fps(scenes_pl, args.fps, probed_fps)
        ae.FPS = max(1, fps)
        log(f"• FPS: {ae.FPS} ({fps_why})")

        # Choose encoder + jobs
        import os as _os
        cpu = _os.cpu_count() or 4
        enc, jobs = choose_encoder_jobs(args.encoder, cpu, args.jobs)
        ae.ENCODER = enc
        log(f"• Encoder: {enc} | Render song song: {jobs} cảnh/lúc")

        # Determine clip extras (for xfade)
        is_img = [not s.source.lower().endswith(DEFAULT_VIDEO_EXTS) for s in scenes_pl]
        use_xf = (args.transition != "none")
        D = max(0.15, min(args.xfade_duration, 1.5)) if use_xf else 0.0
        n_sc = len(scenes_pl)
        clips = [os.path.join(tmp, f"clip_{i:04d}.mp4") for i in range(n_sc)]
        rlen = []
        for i, sp in enumerate(scenes_pl):
            extra = D if (use_xf and is_img[i] and i + 1 < n_sc and is_img[i + 1]) else 0.0
            rlen.append(sp.duration + extra)

        done = [0]
        plock = threading.Lock()

        def _render_scene(t):
            i, src, d = t
            try:
                ffmpeg_client.build_clip(
                    src, d, clips[i],
                    kenburns=not args.no_kenburns, index=i,
                    clip_fit=args.clip_fit, edge_fade=not use_xf,
                    clip_fade=(args.transition != "none"),
                )
            except SystemExit as e:
                raise SystemExit(f"Cảnh {i+1} ({os.path.basename(src)}): {e}")
            with plock:
                done[0] += 1
                log(f"  [{done[0]}/{n_sc}] {os.path.basename(src)}  ({d:.2f}s)")

        tasks = [(i, sp.source, rlen[i]) for i, sp in enumerate(scenes_pl)]
        if jobs <= 1:
            for t in tasks:
                _render_scene(t)
        else:
            with ThreadPoolExecutor(max_workers=jobs) as ex:
                for _ in ex.map(_render_scene, tasks):
                    pass

        # ----------- STAGE 3. CONCAT (silent video) -----------
        silent = ffmpeg_client.concat_or_xfade(
            clips, rlen, is_img, use_xf, D, tmp, args.transition,
        )

        # ----------- STAGE 3b. CLIP AUDIO TRACK (optional) -----------
        clipsnd = None
        if args.keep_clip_audio:
            log("• Tách âm thanh gốc của clip (khớp từng cảnh)...")
            clipsnd = ae.build_clip_audio_track(scenes_pl, tmp, args.clip_fit)
            if not clipsnd:
                log("  (không clip nào có âm thanh — bỏ qua)")

        # ----------- STAGE 3c. SFX TRACK (optional) -----------
        sfxsnd = None
        if args.sfx and os.path.isfile(args.sfx) and len(scenes_pl) > 1:
            log("• Dựng track SFX chuyển cảnh...")
            sfxsnd = ae.build_sfx_track(scenes_pl, tmp, os.path.abspath(args.sfx),
                                        args.sfx_volume)

        # ----------- STAGE 4. FINALIZE (color + sub + voice + bgm + logo) -----------
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        out_abs = os.path.abspath(args.out)
        bgm = None
        if args.bgm and os.path.isdir(args.bgm):
            bgm = ae.build_bgm_playlist(args.bgm, tmp)
        elif args.bgm and os.path.isfile(args.bgm):
            bgm = os.path.abspath(args.bgm)
        vid_dur = ae.probe_duration(silent) or total_end

        # Build vchain (color + vignette + grain + subtitles + title)
        vchain = []
        cg = ae.color_grade_filter(args.color)
        if cg:
            vchain.append(cg)
        if args.vignette:
            vchain.append("vignette=angle=PI/5")
        if args.grain:
            vchain.append("noise=alls=6:allf=t")
        cwd = None
        if not args.no_subtitles:
            subs = os.path.join(tmp, "subs.ass")
            ae._write_ass(args.srt, subs, ae.WIDTH, ae.HEIGHT, args.karaoke_color,
                          font=args.sub_font, mode=args.sub_mode,
                          outline_color=args.sub_outline_color, size=args.sub_size)
            cwd = tmp
            vchain.append("subtitles=subs.ass")
        if args.title_text and args.title_text.strip():
            tass = os.path.join(tmp, "title.ass")
            ae._write_title_ass(tass, ae.WIDTH, ae.HEIGHT,
                                args.title_text.strip(),
                                seconds=args.title_sec, font=args.sub_font)
            cwd = tmp
            vchain.append("subtitles=title.ass")

        # Logo shape (round/circle processing)
        logo = (os.path.abspath(args.logo)
                if (args.logo and os.path.isfile(args.logo)) else None)
        logo_ready = False
        if logo and args.logo_shape != "square":
            _rnd = os.path.join(tmp, "logo_shape.png")
            _size = max(24, args.logo_size)
            if args.logo_shape == "circle":
                _vf = (f"scale=-1:{_size},crop='min(iw,ih)':'min(iw,ih)',format=rgba,"
                       "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                       "a='alpha(X,Y)*clip(W/2-hypot(X-(W-1)/2,Y-(H-1)/2)+0.5,0,1)'")
            else:
                _vf = (f"scale=-1:{_size},format=rgba,"
                       "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                       "a='alpha(X,Y)*clip(H/5-hypot(max(max(H/5-X,X-W+1+H/5),0),"
                       "max(max(H/5-Y,Y-H+1+H/5),0))+0.5,0,1)'")
            try:
                run_cmd([ae.FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                         "-i", logo, "-vf", _vf, "-frames:v", "1", _rnd], timeout=120)
                if os.path.isfile(_rnd):
                    logo, logo_ready = _rnd, True
            except SystemExit:
                pass

        ffmpeg_client.compose_final(
            silent_path=silent, out_path=out_abs,
            voice=voice, bgm=bgm, clipsnd=clipsnd, sfxsnd=sfxsnd,
            logo=logo, logo_ready=logo_ready, vchain=vchain, cwd=cwd,
            voice_volume=args.voice_volume, bgm_volume=args.bgm_volume,
            clip_volume=args.clip_volume, logo_opacity=args.logo_opacity,
            logo_pos=args.logo_pos, logo_size=args.logo_size,
            no_duck=args.no_duck, encoder=enc, vid_dur=vid_dur,
            FFMPEG=ae.FFMPEG, enc_args_fn=ae.enc_args,
        )
        log(f"  • Render thành công: {os.path.basename(out_abs)}")

        # Optional: intro/outro
        if ((args.intro and os.path.isfile(args.intro))
                or (args.outro and os.path.isfile(args.outro))):
            log("• Ghép intro/outro vào video...")
            ae._attach_intro_outro(out_abs, args.intro, args.outro, tmp)

        log("\n" + f"✅ XONG: {out_abs}")
        if audio_dur and segs[-1]['end'] < audio_dur - 0.5:
            log(f"  (Voice dài {audio_dur:.1f}s > SRT {segs[-1]['end']:.1f}s — "
                "ảnh cuối đã được kéo dài để phủ hết tiếng.)")
    finally:
        if args.keep_temp:
            log(f"• Temp giữ lại tại: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    return True


# ---------------------------------------------------------------------------
# Internal: build a `SimpleNamespace`-style args object (like argparse) so the
# downstream calls (auto_edit._write_ass, ae.enc_args, ...) keep working.
# ---------------------------------------------------------------------------
def _build_args(srt_path: str, img_dir: str, out_path: str, cfg: dict) -> types.SimpleNamespace:
    """Build a config namespace compatible with old code expectations."""
    defaults = {
        "input_dir": "input", "voice": None, "image_mode": "auto", "scenes": None,
        "seconds_per_image": None, "dry_run": False, "clip_fit": "auto",
        "transition": "none", "xfade_duration": 0.5, "fps": None,
        "no_kenburns": False, "no_subtitles": False, "karaoke_color": "#FFFF00",
        "sub_font": None, "sub_mode": "word", "sub_outline_color": None,
        "sub_size": 52, "keep_clip_audio": False, "clip_volume": 0.25,
        "voice_volume": 1.0, "aspect": "16:9", "logo": None, "logo_pos": "br",
        "logo_size": 96, "logo_opacity": 0.85, "logo_shape": "round",
        "title_text": None, "title_sec": 4.0, "intro": None, "outro": None,
        "sfx": None, "sfx_volume": 0.5, "color": "none", "vignette": False,
        "grain": False, "bgm": None, "bgm_volume": 0.18, "no_duck": False,
        "keep_temp": False, "max_scenes": None, "encoder": "auto", "jobs": None,
    }
    merged = dict(defaults)
    merged.update({k: v for k, v in cfg.items() if k in defaults})
    return types.SimpleNamespace(
        srt=srt_path, images=img_dir, out=out_path, **merged,
    )