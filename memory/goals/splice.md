# Splice - Cycle 25 Goals (Fleet Autonomy Convergence)
Proposed 2026-11-26. Theme: make media pipelines self-sufficient, auto-QC'd, zero-touch from Lumen/Reel render to platform-ready output.

## Goals

1. **Auto-ingest pipeline** - Watch `memory/designer/reel/` and `memory/designer/lumen/` for new renders; on detection, run a standard ingest (probe -> normalize -> stage) without human trigger. Acceptance: drop a file in reel output dir, see it appear in splice staging within 60s unattended.

2. **Format ladder generator** - Given one master render, auto-produce the full platform ladder (1080p/720p/480p MP4 + 9:16 vertical crop + thumbnail frame) per outlet's platform registry. Acceptance: single ffmpeg graph produces all variants; output manifest lists each with duration/resolution/bitrate.

3. **Loudness auto-normalize** - Every video output passes through EBU R128 loudness normalization (-14 LUFS target, -1 dBTP ceiling) as a mandatory pipeline stage. Acceptance: `ffprobe` + `loudnorm` measurement on any splice output shows -14 ± 1 LUFS integrated.

4. **Frame-accurate QC gate** - Automated post-render check: duration matches expected (±1 frame), no black frames at head/tail, resolution matches target, audio present if master has audio. Fail = quarantine file + log. Acceptance: inject a bad render (wrong duration), pipeline quarantines it and writes a QC report.

5. **Subtitle burn-in from transcript** - Given an SRT/VTT file (from Outlet's caption pass or Whisper output), burn subtitles with safe-area margins per platform spec. Acceptance: input video + SRT -> output with readable captions, no clipping at 16:9 or 9:16.

6. **Versioned output registry** - Every splice output gets a deterministic name (`YYYY-MM-DD_<purpose>_<source-sha8>.mp4`) and is logged in `memory/designer/splice/registry.jsonl` with input provenance, pipeline version, QC result. Acceptance: any output file can be traced back to its source + pipeline run in <5s via registry lookup.

7. **Batch splice (multi-source)** - Given N source clips + an edit decision list (JSON: in/out points per clip), produce a single stitched output with crossfade transitions. Acceptance: 3-clip EDL -> one output, transitions visible, total duration = sum(clips) - overlap.

8. **Pipeline self-heal** - If ffmpeg fails mid-pipeline (codec missing, disk full, timeout), log the exact error, retry once with fallback settings (e.g., libx264 -> mpeg4), and only escalate to human if both attempts fail. Acceptance: simulate a codec failure, pipeline retries with fallback and succeeds.

9. **Thumbnail + preview frame extraction** - Auto-extract 3 candidate thumbnail frames (10%, 50%, 90% of duration) for each output; write them as PNGs alongside the video. Outlet can pick one without re-running ffmpeg. Acceptance: any splice output has exactly 3 `.thumb_*.png` files in same dir.

10. **Cycle-25 integration test** - End-to-end: Reel produces a 10s clip -> Splice ingests, normalizes loudness, produces format ladder + thumbnails + QC report -> Outlet picks a thumbnail and posts. Zero human intervention between Reel render-complete and Outlet-ready. Acceptance: full chain runs in <5min wall-clock, all artifacts present.

## Notes
- Goals 1-4 are the autonomy core (no human in loop for standard renders).
- Goal 10 is the convergence proof - it exercises goals 1,2,3,4,9 together.
- Depends on: Reel having a stable output dir convention (coordinate with Designer), Outlet platform registry being current.
- No source files are ever modified; all outputs go to `memory/designer/splice/outputs/` or outlet staging.
