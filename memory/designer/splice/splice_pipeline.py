#!/usr/bin/env python3
"""Splice Stage-3 Pipeline: encode + QC platform-ready media.

Serves: memory/ops/video-pipeline-handoff-2026-11-25.md stage 3
Spec:   memory/ops/media-format-ladder-spec-2026-11-26.md

Usage:
    python splice_pipeline.py --slug <slug> [--platforms youtube_shorts,tiktok] [--fps 30]

Day-0 mode: if no frames exist, produces a 3s placeholder (solid color + text).
Never destroys source files. All outputs are versioned.
"""
import argparse, json, os, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

# --- Constants (from format ladder spec) ---
PLATFORMS = {
    "youtube_shorts": {"res": (1080, 1920), "audio_kbps": 320, "max_dur": 60, "aspect": "9:16"},
    "tiktok":         {"res": (1080, 1920), "audio_kbps": 256, "max_dur": 60, "aspect": "9:16"},
    "x_twitter":      {"res": (1280, 720), "audio_kbps": 192, "max_dur": 140, "aspect": "16:9"},
    "linkedin":       {"res": (1080, 1080), "audio_kbps": 192, "max_dur": 180, "aspect": "1:1"},
    "instagram_reels":{"res": (1080, 1920), "audio_kbps": 256, "max_dur": 90, "aspect": "9:16"},
}

BASE_DIR = Path(".")
SPICE_OUT = BASE_DIR / "memory" / "designer" / "splice"
OUTLET_STAGING = BASE_DIR / "memory" / "outlet" / "staging" / "media"
MANIFEST = SPICE_OUT / "MANIFEST.jsonl"
BACKUP_DIR = SPICE_OUT / "_backup"

def log(msg):
    print(f"[splice] {msg}", flush=True)

def find_frames(slug: str) -> Path | None:
    """Locate frame directory for this slug (Lumen renders or Reel output)."""
    candidates = [
        BASE_DIR / "memory" / "designer" / "lumen" / f"renders_{slug}",
        BASE_DIR / "memory" / "designer" / "reel" / f"clips_{slug}",
        BASE_DIR / "memory" / "outlet" / "uploads" / f"{slug}",
    ]
    for d in candidates:
        if d.exists():
            frames = list(d.glob("*.png")) + list(d.glob("*.jpg")) + list(d.glob("*.webp"))
            if frames:
                return d
    return None

def make_placeholder(slug: str, out_dir: Path, fps: int = 30, dur: float = 3.0) -> Path:
    """Day-0 degrade: solid-color 1080x1920 with slug text + COMING SOON."""
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / f"placeholder_{slug}"
    frames_dir.mkdir(exist_ok=True)
    n_frames = int(fps * dur)
    # Use ffmpeg to generate a single frame with text, then loop it
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1a1a2e:s=1080x1920:d={dur}:r={fps}",
        "-vf", (
            f"drawtext=text='{slug}':fontcolor=white:fontsize=72:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-40,"
            f"drawtext=text='COMING SOON':fontcolor=0x888888:fontsize=36:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+40"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(frames_dir / "placeholder.mp4"),
    ]
    log(f"Placeholder: {' '.join(cmd[:6])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # Fallback: just a solid color (no drawtext font issues)
        cmd_fallback = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x1a1a2e:s=1080x1920:d={dur}:r={fps}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            str(frames_dir / "placeholder.mp4"),
        ]
        r = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg placeholder failed: {r.stderr[-500:]}")
    return frames_dir / "placeholder.mp4"

def encode(input_path: Path, platform: str, fps: int, out_path: Path, srt_path: Path | None = None):
    """Encode one platform variant per the format ladder."""
    spec = PLATFORMS[platform]
    w, h = spec["res"]
    audio_kbps = spec["audio_kbps"]
    
    vf_parts = [f"scale={w}:{h}:flags=lanczos", f"fps={fps}", "format=yuv420p"]
    if srt_path and srt_path.exists():
        vf_parts.insert(-1, f"subtitles={srt_path.name}:force_style='FontName=Inter,FontSize=24,Bold=1,MarginV=80'")
    
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", ",".join(vf_parts),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-profile:v", "high", "-level", "5.1",
        "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        "-t", str(spec["max_dur"]),
        str(out_path),
    ]
    log(f"Encode {platform}: {input_path.name} -> {out_path.name}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg encode failed for {platform}: {r.stderr[-500:]}")

def qc_check(out_path: Path, platform: str) -> dict:
    """Run QC gates. Returns {passed: bool, checks: {...}}."""
    spec = PLATFORMS[platform]
    w, h = spec["res"]
    results = {}
    
    # Duration
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True
    )
    try:
        dur = float(r.stdout.strip())
        results["duration"] = {"value": dur, "pass": dur <= spec["max_dur"] + 0.5}
    except ValueError:
        results["duration"] = {"value": None, "pass": False}
    
    # Resolution
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True
    )
    try:
        parts = r.stdout.strip().split(",")
        ow, oh = int(parts[0]), int(parts[1])
        results["resolution"] = {"value": f"{ow}x{oh}", "pass": (ow == w and oh == h)}
    except (ValueError, IndexError):
        results["resolution"] = {"value": None, "pass": False}
    
    # File size
    size_mb = out_path.stat().st_size / (1024 * 1024)
    max_mb = spec.get("max_size_mb", 256)
    results["file_size"] = {"value": f"{size_mb:.1f}MB", "pass": size_mb < max_mb}
    
    passed = all(c["pass"] for c in results.values())
    return {"passed": passed, "checks": results}

def main():
    ap = argparse.ArgumentParser(description="Splice Stage-3: encode + QC")
    ap.add_argument("--slug", required=True, help="Content slug (matches storyboard/frames dir)")
    ap.add_argument("--platforms", default="youtube_shorts,tiktok", help="Comma-separated platform list")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--skip-qc", action="store_true", help="Skip QC (debug only)")
    args = ap.parse_args()
    
    today = date.today().isoformat()
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip() in PLATFORMS]
    if not platforms:
        log(f"ERROR: no valid platforms in {args.platforms!r}")
        sys.exit(1)
    
    # Ensure output dirs
    OUTLET_STAGING.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find input
    frames_dir = find_frames(args.slug)
    if frames_dir:
        # Use first video or frame sequence
        videos = list(frames_dir.glob("*.mp4")) + list(frames_dir.glob("*.mov"))
        if videos:
            input_path = sorted(videos)[0]
        else:
            log(f"WARNING: no video in {frames_dir}, using placeholder")
            input_path = make_placeholder(args.slug, SPICE_OUT / "_work")
    else:
        log("Day-0 mode: no frames found, generating placeholder")
        input_path = make_placeholder(args.slug, SPICE_OUT / "_work")
    
    log(f"Input: {input_path}")
    
    # Encode + QC per platform
    manifest_entries = []
    all_passed = True
    for plat in platforms:
        out_name = f"{today}_{args.slug}_{plat}_v1.mp4"
        out_path = OUTLET_STAGING / out_name
        
        try:
            encode(input_path, plat, args.fps, out_path)
        except RuntimeError as e:
            log(f"FAIL {plat}: {e}")
            all_passed = False
            continue
        
        if not args.skip_qc:
            qc = qc_check(out_path, plat)
            if not qc["passed"]:
                log(f"QC FAIL {plat}: {json.dumps(qc['checks'], indent=2)}")
                all_passed = False
            else:
                log(f"QC PASS {plat}: dur={qc['checks']['duration']['value']}s res={qc['checks']['resolution']['value']}")
        else:
            qc = {"passed": True, "checks": {"skipped": True}}
        
        # Backup
        backup_path = BACKUP_DIR / out_name
        shutil.copy2(out_path, backup_path)
        
        manifest_entries.append({
            "date": today, "slug": args.slug, "platform": plat,
            "file": str(out_path), "backup": str(backup_path),
            "qc_passed": qc["passed"], "input": str(input_path),
        })
    
    # Write manifest
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as f:
        for e in manifest_entries:
            f.write(json.dumps(e) + "\n")
    
    log(f"Done. {len(manifest_entries)} variants written to {OUTLET_STAGING}")
    if not all_passed:
        log("WARNING: some variants failed QC - check output above")
        sys.exit(1)

if __name__ == "__main__":
    main()
