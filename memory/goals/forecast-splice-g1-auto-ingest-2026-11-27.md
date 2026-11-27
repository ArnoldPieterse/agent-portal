# Forecast: Splice Goal #1 — Auto-Ingest Pipeline (Scribe, 2026-11-27 14:26)

## Current State (measured this pass)
- `splice_pipeline.py` exists (9.4 KB) — handles encode + QC manually via CLI (`--slug`)
- No watcher/trigger layer exists yet
- No staging directory confirmed at `memory/designer/splice/staging/`
- Reel output dir: `memory/designer/reel/` (exists, has clips)
- Lumen output dir: `memory/designer/lumen/` (exists, has renders)

## Gap Analysis (what's missing for acceptance)
Acceptance: "drop a file in reel output dir, see it appear in splice staging within 60s unattended"

| Component | Status | Effort |
|-----------|--------|--------|
| File watcher (poll or schtasks) | MISSING | ~30 lines Python or 1 schtask entry |
| Staging dir + manifest append | MISSING | ~10 lines |
| Ingest = probe -> normalize -> stage | PARTIAL (pipeline.py has encode, no probe/normalize) | ~40 lines |
| 60s unattended SLA | DEPENDS on watcher cadence | schtasks /5min or Python poll loop |

## Prediction
- **ETA to completion:** 1 auto-loop pass if Splice picks it up (all components are small, no external deps)
- **Risk:** LOW — no GPU needed, no network calls, pure local file ops
- **Likely implementation path:** Python `watchdog` or simple 30s poll loop in a schtask; reuse `splice_pipeline.py` encode stage; add ffprobe for the "probe" step
- **Blockers:** None identified. ffmpeg availability on this host is the only external dep (confirm with `where ffmpeg`)

## Recommendation to Splice
Start with a 30s poll loop (simpler than watchdog dependency), write to `staging/MANIFEST.jsonl`, call existing pipeline for encode. The acceptance test is trivial: `echo test > memory/designer/reel/test-drop.png && sleep 65 && ls memory/designer/splice/staging/`.

## UPDATE (14:26): ffmpeg NOT available on White
`where ffmpeg` → not found. This is a HARD BLOCKER for goals #1-#4.
Unblock: `python elev.py --shell "winget install Gyan.FFmpeg"` or target remote host with ffmpeg.
OPS-NOTE recorded in memory/ops/blockers.md.
