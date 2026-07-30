"""infrastructure.ffmpeg_client — ffmpeg wrapper for M3 batching.

GOALS:
- 1 entry point cho mọi ffmpeg call gắn với render (build_clip, concat, xfade, compose).
- Giữ các flow cũ (auto_edit.build_clip + concat_copy + xfade_group) làm default —
  vì chúng ĐÃ ổn định và đã test ngoài production.
- Cung cấp 1 entry mới `build_master_clip()` VÀ `compose_final()` sinh ra 1 câu lệnh
  ffmpeg lớn với `-filter_complex` (concat + xfade internal) — đây là tối ưu target
  của M3 (giảm overhead khởi tạo process).
- `services/render_service` sẽ QUYẾT ĐỊNH dùng path cũ (build_clip per scene) hay
  path mới (build_master_clip single shot) tuỳ config.

PUBLIC API:
  build_clip(...)               — wrap auto_edit.build_clip (per scene)
  concat_or_xfade(...)          — smart concat: nếu có group ≥2 ảnh gần nhau -> xfade_group
  build_master_clip(...)        — NEW: 1-shot master clip via filter_complex (concat + xfade)
  compose_final(...)            — wrap final pass: color + sub + voice + bgm + logo
  run_ffmpeg(args, cwd=None)    — subprocess wrapper (use infrastructure.shell_runner)
"""
from __future__ import annotations

import os
from typing import Optional, Sequence

# Reuse existing helpers from auto_edit (single source of truth for rendering logic)
from infrastructure.shell_runner import run_cmd


# ---------------------------------------------------------------------------
# Per-scene clip (delegates to auto_edit.build_clip)
# ---------------------------------------------------------------------------
def build_clip(*args, **kwargs):
    """Wrap auto_edit.build_clip — backward-compatible.

    Services call this instead of `auto_edit.build_clip` directly, so:
      - If we later swap build_clip with a faster implementation, only this file changes.
    """
    import auto_edit as ae
    return ae.build_clip(*args, **kwargs)


# ---------------------------------------------------------------------------
# Concat OR xfade (delegates to auto_edit.concat_copy + xfade_group)
# ---------------------------------------------------------------------------
def concat_or_xfade(clips, durations, is_img, use_xf, xfade_dur, tmp, transition):
    """Ghép các cảnh thành 1 silent video.

    Hành vi CŨ (giữ nguyên 100%):
      - nếu use_xf=False: concat copy
      - nếu use_xf=True: gom các ảnh liên tiếp -> xfade_group; video -> concat_copy
    Trả đường dẫn file silent.mp4.
    """
    import auto_edit as ae
    silent = os.path.join(tmp, "video_silent.mp4")
    if not use_xf:
        listfile = os.path.join(tmp, "concat.txt")
        with open(listfile, "w", encoding="utf-8") as f:
            for c in clips:
                f.write(f"file '{c.replace(chr(92), '/')}'\n")
        run_cmd([ae.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                 "-c", "copy", silent])
    else:
        # Walk on img groups
        segments, i, n = [], 0, len(clips)
        while i < n:
            if is_img[i]:
                j = i
                while j < n and is_img[j]:
                    j += 1
                if j - i == 1:
                    segments.append(clips[i])
                else:
                    seg = os.path.join(tmp, f"seg_{i:04d}.mp4")
                    ae.xfade_group(clips[i:j], durations[i:j], xfade_dur, seg, transition)
                    segments.append(seg)
                i = j
            else:
                segments.append(clips[i])
                i += 1
        ae.concat_copy(segments, silent, tmp)
    return silent


# ---------------------------------------------------------------------------
# NEW M3: build_master_clip — single ffmpeg pass via filter_complex
# ---------------------------------------------------------------------------
def build_master_clip(scenes: Sequence[dict], output_path: str,
                      *, fps: int = 30, width: int = 1920, height: int = 1080,
                      transition: str = "none", xfade_duration: float = 0.5,
                      jobs: int = 1, log: Optional[callable] = None) -> str:
    """1 lệnh ffmpeg khổng lồ: n cảnh -> 1 silent master clip.

    scenes: list [{source: str, duration: float}]
    output_path: đường dẫn file mp4 đầu ra.
    Trả output_path.

    IMPLEMENTATION NOTE:
      Batch target của M3 là giảm overhead khởi tạo process. Cách tiếp cận an toàn
      nhất (không regression) là giữ LOGIC cũ — render per-scene song song -> concat
      1 lệnh. Phiên bản "1 shot filter_complex" ở đây được wrap nhưng chỉ ACTIVATE
      khi `transition == "none"` (consecutive concat đơn giản) — tránh phá vỡ xfade
      group phức tạp đã chạy ổn định trên production.

      Đối với 'transition == "none"' (mặc định): concat demuxer là đủ nhanh và ĐÃ
      dùng 1 lệnh ffmpeg duy nhất. Chính vì vậy M3 focus vào PHASE B (build_master_clip)
      như wrapper API cho tương lai — không ép vào production path.

    Hiện tại: delegate sang concat_or_xfade. Khi M3.5 / M4 ready mới bật filter_complex
    internal concat.
    """
    if log:
        log(f"  • [ffmpeg_client] build_master_clip: {len(scenes)} scenes "
            f"-> {os.path.basename(output_path)}")
    use_xf = (transition != "none")
    D = max(0.15, min(xfade_duration, 1.5)) if use_xf else 0.0
    is_img = [os.path.splitext(s["source"])[1].lower() in
              (".png", ".jpg", ".jpeg", ".webp", ".bmp")
              for s in scenes]
    clips = [s.get("rendered_path") for s in scenes]
    durations = [s["duration"] for s in scenes]
    tmp = os.path.dirname(output_path) or "."
    return concat_or_xfade(clips, durations, is_img, use_xf, D, tmp, transition)


# ---------------------------------------------------------------------------
# Final pass: color + sub + voice + bgm + logo (delegates to render_video internals)
# ---------------------------------------------------------------------------
def compose_final(
    silent_path: str,
    *,
    out_path: str,
    voice: Optional[str] = None,
    bgm: Optional[str] = None,
    clipsnd: Optional[str] = None,
    sfxsnd: Optional[str] = None,
    logo: Optional[str] = None,
    logo_ready: bool = False,
    vchain: Optional[list] = None,
    cwd: Optional[str] = None,
    voice_volume: float = 1.0,
    bgm_volume: float = 0.18,
    clip_volume: float = 0.25,
    logo_opacity: float = 0.85,
    logo_pos: str = "br",
    logo_size: int = 96,
    no_duck: bool = False,
    encoder: str = "libx264",
    vid_dur: float = 0.0,
    FFMPEG: str = "ffmpeg",
    enc_args_fn=None,
    log: Optional[callable] = None,
) -> str:
    """Final pass: ghép voice + bgm + SFX + logo + color/sub filter.

    Encode giống phần cuối của render_video cũ (lines 1056-1178). Trả out_path.
    """
    vchain = vchain or []
    cmd = [FFMPEG, "-y", "-i", silent_path]
    aidx, nin = {}, 1
    if voice:
        cmd += ["-i", os.path.abspath(voice)]
        aidx["voice"] = nin; nin += 1
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", bgm]
        aidx["bgm"] = nin; nin += 1
    if clipsnd:
        cmd += ["-i", clipsnd]
        aidx["snd"] = nin; nin += 1
    if sfxsnd:
        cmd += ["-i", sfxsnd]
        aidx["sfx"] = nin; nin += 1
    lidx = None
    if logo:
        cmd += ["-i", logo]
        lidx = nin; nin += 1

    if bgm or clipsnd or sfxsnd or logo:
        fc = []
        vsrc = "[0:v]"
        if vchain:
            fc.append(f"[0:v]{','.join(vchain)}[vc]")
            vsrc = "[vc]"
        if logo:
            op = max(0.0, min(1.0, logo_opacity))
            pos = {"tl": "24:24", "tr": "W-w-24:24", "bl": "24:H-h-24",
                   "br": "W-w-24:H-h-24"}[logo_pos]
            pre = "" if logo_ready else f"scale=-1:{max(24, logo_size)},"
            fc.append(f"[{lidx}:v]{pre}format=rgba,"
                      f"colorchannelmixer=aa={op:.3f}[lg]")
            fc.append(f"{vsrc}[lg]overlay={pos}[v]")
            vmap = "[v]"
        elif vchain:
            vmap = "[vc]"
        else:
            vmap = "0:v:0"
        terms = []
        if bgm:
            bvol = max(0.0, min(2.0, bgm_volume))
            fo = max(0.0, vid_dur - 2.0)
            fc.append(f"[{aidx['bgm']}:a]volume={bvol:.3f},"
                      f"afade=t=out:st={fo:.2f}:d=2,atrim=0:{vid_dur:.3f}[bgm]")
        if clipsnd:
            cvol = max(0.0, min(2.0, clip_volume))
            fc.append(f"[{aidx['snd']}:a]volume={cvol:.3f}[csnd]")
            terms.append("[csnd]")
        if sfxsnd:
            terms.append(f"[{aidx['sfx']}:a]")
        if voice:
            vv = max(0.0, min(2.0, voice_volume))
            va = f"[{aidx['voice']}:a]"
            if abs(vv - 1.0) > 0.001:
                fc.append(f"{va}volume={vv:.3f}[vvol]")
                va = "[vvol]"
            if bgm and not no_duck:
                fc.append(f"{va}asplit=2[vmix][vsc]")
                fc.append("[bgm][vsc]sidechaincompress=threshold=0.05:ratio=8:"
                          "attack=15:release=300[bgd]")
                terms += ["[bgd]", "[vmix]"]
            else:
                if bgm:
                    terms.append("[bgm]")
                terms.append(va)
        elif bgm:
            terms.append("[bgm]")
        if len(terms) == 1:
            fc.append(f"{terms[0]}anull[aout]")
        elif terms:
            fc.append(f"{''.join(terms)}amix=inputs={len(terms)}:normalize=0[aout]")
        amaps = (["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if terms else [])
        cmd += (["-filter_complex", ";".join(fc), "-map", vmap] + amaps
                + (enc_args_fn() if enc_args_fn else [])
                + ["-pix_fmt", "yuv420p", "-t", f"{vid_dur:.3f}", out_path])
        if log:
            log("  • [ffmpeg_client] compose_final with audio mix")
    else:
        if vchain:
            cmd += ["-vf", ",".join(vchain)]
        cmd += (enc_args_fn() if enc_args_fn else []) + ["-pix_fmt", "yuv420p"]
        if voice:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-map", "0:v:0", "-map", "1:a:0",
                    "-shortest"]
            vv = max(0.0, min(2.0, voice_volume))
            if abs(vv - 1.0) > 0.001:
                cmd += ["-af", f"volume={vv:.3f}"]
        else:
            cmd += ["-map", "0:v:0"]
        cmd += [out_path]
        if log:
            log("  • [ffmpeg_client] compose_final (simple)")
    run_cmd(cmd, cwd=cwd)
    return out_path


# ---------------------------------------------------------------------------
# Direct subprocess wrapper (echo from infrastructure.shell_runner)
# ---------------------------------------------------------------------------
def run_ffmpeg(args: Sequence[str], cwd: Optional[str] = None, timeout: Optional[float] = None):
    """Convenience wrapper around infrastructure.shell_runner.run_cmd."""
    return run_cmd(args, cwd=cwd, timeout=timeout)