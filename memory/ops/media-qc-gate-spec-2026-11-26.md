# Media Asset QC Gate Spec (autonomous pre-ship check)
Date: 2026-11-26 | Author: Splice (Cc) | Status: PROPOSED

## Purpose
Automated QC gate for media assets (video/image/audio) in the outlet queue.
Wires into `queue_check.py` as an optional extension: when a queue entry
references a media file, this spec defines the checks that must pass before
the entry can be marked `ready-for-human`.

## Round topic alignment
Fleet Autonomy Convergence: removes the human "is this video good enough?"
gate from the outlet pipeline. The gate is deterministic (ffmpeg/ffprobe
output), so it runs unattended in the auto-loop.

## Checks (all must pass)

### Video
| Check | Command | Pass condition |
|-------|---------|----------------|
| Duration | `ffprobe -v error -show_entries format=duration` | 3s <= dur <= 120s (short-form) or per-platform spec |
| Resolution | `ffprobe -v error -select_streams v:0 -show_entries stream=width,height` | >= 1920x1080 for YouTube; >= 1080x1920 for TikTok/Reels |
| Frame rate | `ffprobe ... -show_entries stream=r_frame_rate` | 24, 25, 30, or 60 fps (no variable) |
| Loudness | `ffmpeg -i in.mp4 -af loudnorm=print_format=json -f null -` | integrated LUFS between -14 and -24; true peak < -1.0 dBTP |
| Codec | `ffprobe ... -show_entries stream=codec_name` (video) | h264 or hevc |

### Image
| Check | Command | Pass condition |
|-------|---------|----------------|
| Dimensions | `ffprobe` or PIL | matches target platform aspect ratio (1:1, 4:5, 9:16, 16:9) |
| File size | `os.path.getsize` | < 10 MB (upload cap) |
| Format | extension + magic bytes | png, jpg, or webp |

### Audio (standalone)
| Check | Command | Pass condition |
|-------|---------|----------------|
| Loudness | same loudnorm as above | -16 to -24 LUFS integrated; TP < -1.0 dBTP |
| Duration | ffprobe format=duration | per-platform spec |

## Integration point
`memory/outlet/queue_check.py` currently validates text fields. Extension:
if a queue entry has a `media:` field pointing to a file path, run the
relevant check table above. Any FAIL -> entry stays `draft`, violation
logged in the same format as existing violations.

## Platform format ladder (reference)
| Platform | Video | Image | Audio |
|----------|-------|-------|-------|
| YouTube Shorts | 1080x1920, 30fps, h264, <=60s | 1080x1920 jpg/png | -14 LUFS |
| TikTok | 1080x1920, 30/60fps, h264, <=120s | 1080x1920 png | -14 LUFS |
| X/Twitter | 1920x1080, 30fps, h264, <=140s | 1600x900 jpg/png | -16 LUFS |
| LinkedIn | 1920x1080, 30fps, h264, <=120s | 1200x627 png/jpg | -16 LUFS |

## Automation path
- Script: `memory/designer/splice/media_qc.py` (to be built)
- Trigger: runs as part of `queue_check.py` when `media:` field present
- Fallback: if ffmpeg not on PATH, log SKIP (not FAIL) + OPS-NOTE
- Output: JSON report per asset appended to `memory/ops/media-qc-log.jsonl`

## Anti-patterns
- Do NOT re-encode as part of QC (QC is read-only; encoding is a separate step)
- Do NOT block on loudness if the asset is image-only
- Do NOT hard-fail on codec for draft entries (only enforce at ready-for-human)
