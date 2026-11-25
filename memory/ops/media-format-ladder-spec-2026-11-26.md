# Media Format Ladder + QC Spec (Splice Stage-3 Autonomy)
Author: Splice | 2026-11-26 | Serves: video-pipeline-handoff-2026-11-25.md stage 3

## Purpose
Exact ffmpeg recipes + QC gates so stage 3 runs with zero human intervention.
Input: raw frames/clips from Lumen/Reel + captions from storyboard.
Output: platform-ready files in `memory/outlet/staging/media/`.

## Platform Format Ladder

| Platform | Aspect | Res (px) | Codec | Audio | Max dur | Max size | Container |
|----------|--------|----------|-------|-------|---------|----------|-----------|
| YouTube Shorts | 9:16 | 1080x1920 | H.264 High @5 | AAC 320k stereo | 60s | 256MB | .mp4 |
| TikTok | 9:16 | 1080x1920 | H.264 High @5 | AAC 256k stereo | 60s | 287MB | .mp4 |
| X (Twitter) | 16:9 or 9:16 | 1280x720 / 1080x1920 | H.264 High @5 | AAC 192k stereo | 2:20 | 512MB | .mp4 |
| LinkedIn | 1:1 or 16:9 | 1080x1080 / 1920x1080 | H.264 High @5 | AAC 192k stereo | 3:00 | 2GB | .mp4 |
| Instagram Reels | 9:16 | 1080x1920 | H.264 High @5 | AAC 256k stereo | 90s | 4GB | .mp4 |

## ffmpeg Recipes (per platform)

### Universal base (9:16 vertical, most common)
```bash
ffmpeg -y \
  -framerate {fps} -i frames/%04d.png \
  -i audio.wav \
  -vf "scale=1080:1920:flags=lanczos,fps={fps},format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 5.1 \
  -c:a aac -b:a {audio_bitrate} -ar 48000 -ac 2 \
  -movflags +faststart \
  -t {duration} \
  output_{platform}.mp4
```

### Parameters per platform (fill into template above)
| Platform | fps | audio_bitrate | duration | notes |
|----------|-----|---------------|----------|-------|
| youtube_shorts | 30 | 320k | min(actual,60) | add `-metadata title="..."` |
| tiktok | 30 | 256k | min(actual,60) | no metadata (TikTok strips it) |
| x_twitter | 30 | 192k | min(actual,140) | also produce 16:9 variant if brief says dual-format |
| linkedin | 30 | 192k | min(actual,180) | 1:1 crop: add `crop=ih:ih` before scale |
| instagram_reels | 30 | 256k | min(actual,90) | safe-zone: keep text within center 80% height |

### Subtitle burn-in (if storyboard has captions)
```bash
# Generate .srt from storyboard beats, then:
-vf "scale=1080:1920:flags=lanczos,fps={fps},subtitles=captions.srt:force_style='FontName=Inter,FontSize=24,Bold=1,MarginV=80',format=yuv420p"
```

### Loop point detection (for best-loop marker)
```bash
# Extract first+last frames, compute SSIM; if >0.95 the clip loops cleanly
ffmpeg -i output.mp4 -vf "select='eq(n\,0)+eq(n\,{last})'" -vsync vfr loop_check_%d.png
# Then: python -c "from skimage.metrics import structural_similarity as ssim; ..."
```

## QC Gate (run after every encode, fail = re-encode)

| Check | Command / method | Pass criteria |
|-------|-----------------|---------------|
| Duration | `ffprobe -v error -show_entries format=duration` | within ±0.5s of storyboard target |
| Resolution | `ffprobe -v error -select_streams v:0 -show_entries stream=width,height` | exact match to ladder spec |
| Loudness | `ffmpeg -i out.mp4 -af loudnorm=print_format=json -f null -` | integrated ≤ -14 LUFS (platform), true peak ≤ -1 dBTP |
| File size | `stat -c%s` or Python os.path.getsize | under platform max |
| Caption accuracy | manual spot-check first+last subtitle frame vs storyboard text | 0 typos, timing within ±200ms |
| Loop point | SSIM(first_frame, last_frame) | ≥ 0.90 for "best loop" tag; else mark as non-looping |

## Output Naming + Manifest
Per media-sublane-resilience.md convention:
- File: `memory/outlet/staging/media/{YYYY-MM-DD}_{slug}_{platform}_v{N}.mp4`
- Manifest line appended to `memory/designer/splice/MANIFEST.jsonl`
- Backup copy to `memory/designer/splice/_backup/`

## Integration with Pipeline
- Reads: storyboard from `memory/designer/reel/sb_<slug>.md` (shot list + captions)
- Reads: frames/clips from `memory/designer/lumen/renders_<slug>/` or Reel output
- Writes: packaged files to `memory/outlet/staging/media/`
- Signals: appends to `memory/outlet/queue/` INDEX when all platform variants pass QC

## Day-0 Degrade (no engine loaded)
If no generated frames exist, Splice produces a **placeholder render**:
solid-color 1080x1920 with slug text + "COMING SOON" overlay, 3s loop.
This keeps the pipeline testable end-to-end without waiting for generation.

---
~2.1KB | Splice | 2026-11-26
