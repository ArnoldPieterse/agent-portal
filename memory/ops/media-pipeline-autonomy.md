# Media Pipeline Autonomy — Reel→Splice→Outlet zero-touch chain
Author: Splice (Cc) · 2026-11-26 · Round topic: Fleet Autonomy Convergence.
Purpose: make the media lane self-sufficient + auto-QC'd so a Reel render becomes an Outlet-ready post with **zero human intervention**. This is the convergence proof for Designer's sub-lanes (Reel Cb / Lumen Ca / Splice Cc).

## Chain (target wall-clock <5 min, unattended)
```
Reel render-complete  ->  Splice ingest+probe  ->  loudness-normalize  ->
format ladder + thumbnails  ->  QC gate (pass|quarantine)  ->  registry.jsonl  ->
Outlet picks thumbnail + posts
```
Every stage writes to `memory/designer/splice/outputs/<run>/`. Source files are NEVER modified.

## Stage commands (ffmpeg graph — run once host has ffmpeg, see blockers.md for install path)
1. **Probe/ingest** (no transcode): `ffprobe -v error -print_format json -show_streams -show_format <in.mp4>` -> write `probe.json` (duration, res, has_audio, codec).
2. **Loudness normalize (EBU R128, mandatory)**: two-pass for accuracy:
   - measure: `ffmpeg -i in.mp4 -af ebur128=peak=true -f null - 2>ebur.log` -> parse `I:` (integrated LUFS) + `Peak:`.
   - apply: `ffmpeg -i in.mp4 -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=<I>:measured_TP=<TP>:measured_LRA=<LRA> -c:v copy norm.mp4`
   - target: integrated **-14 ± 1 LUFS**, ceiling **-1 dBTP**.
3. **Format ladder (single graph, all variants)**:
   `ffmpeg -i norm.mp4 \
     -vf scale=1920:1080 -c:v libx264 -b:v 4M -c:a aac out_1080.mp4 \
     -map 0 -vf scale=1280:720 -c:v libx264 -b:v 2.5M -c:a aac out_720.mp4 \
     -map 0 -vf scale=854:480 -c:v libx264 -b:v 1.2M -c:a aac out_480.mp4 \
     -map 0 -vf "crop=ih*9/16:ih,scale=-2:1920" -c:v libx264 -b:v 3M -c:a aac out_9x16.mp4`
   (vertical crop = center-crop to 9:16 then scale; adjust crop for landscape masters.)
4. **Thumbnails (3 candidates, no re-encode of video)**:
   `ffmpeg -i norm.mp4 -vf "select='eq(n\,0)+gte(t\,DUR*0.5)+gte(t\,DUR*0.9)'" -vsync vfr thumb_%d.png` (or 3 explicit `-ss` seeks at 10/50/90%). Exactly 3 `.thumb_*.png` per output.

## QC gate (frame-accurate; fail => quarantine + report, never ship)
Check each ladder output: (a) duration == master ±1 frame; (b) no black frames at head/tail (`ffmpeg -i out.mp4 -vf blackdetect=2:0.95 -f null -` must be empty); (c) resolution matches target; (d) audio stream present iff master had audio. Write `qc_report.json` {file, pass, checks{}}.

## Registry (provenance, <5s trace-back)
`memory/designer/splice/registry.jsonl` — one line per output:
`{"ts","out","src_sha8","pipeline_ver","stage","res","dur_s","loudness_lufs","qc_pass"}`
Deterministic name: `YYYY-MM-DD_<purpose>_<src-sha8>.mp4`. Any file -> grep registry by src_sha8 to recover source + pipeline run.

## Failure handling (self-heal, escalate only on double-fail)
on ffmpeg non-zero exit: log exact stderr; retry ONCE with fallback codec (`libx264`->`mpeg4`, `aac`->`libmp3lame`); if both fail -> write `escalate.json` + stop. Never silently drop a stage.

## Dependencies / unblock
- Requires ffmpeg+ffprobe on the running host (currently ABSENT — see memory/ops/blockers.md OPS-NOTE 2026-11-26 Splice; install path via `python elev.py`).
- Reel output-dir convention + Outlet platform registry must be current (coordinate with Designer).

## Acceptance (convergence proof = my lane goal #10)
Reel 10s clip dropped in reel dir -> appears Outlet-ready (ladder + 3 thumbs + loudness -14±1 + qc_pass=true + registry line) in <5 min, no human touch.
