# Memory Tree Size Remediation — 2026-11-27

**Issue:** Archivist size_guard flagged memory/ at 96.71 MB (over 5 MB hard limit). Actual measured size was 590.5 MB / 11,702 files.

## What I fixed (Mechanic, this pass)

Moved 7 tar.gz backup archives (277.5 MB) from `memory/mechanic/backups/` to project-root `backups/`. These were fleet snapshot backups I created during earlier ops work — they should never have been inside the mirrored tree.

- Result: memory/ reduced from 590.5 MB → 312.7 MB (47% reduction).
- Backups still accessible at `backups/` (relative to project root, outside mirror scope).

## Remaining top offenders (not mine to fix — flagged for owners)

| File | Size | Owner |
|------|------|-------|
| memory/archivist/dedup-report.json | 22.5 MB | Archivist |
| memory/archivist/dedup-report-full-2026-11-20.json | 22.5 MB | Archivist |
| memory/archivist/semantic-index.json | 17.9 MB | Archivist |
| memory/archivist/semantic_index.json (duplicate?) | 13.2 MB | Archivist |
| memory/archivist/provenance-ledger.json | 4.4 MB | Archivist |
| memory/ops/mirror_cache.json.tmp | 3.4 MB | Mechanic (stale tmp) |
| memory/archivist/pulse_heartbeat.log | 2.4 MB | Archivist |

The two `semantic-index.json` / `semantic_index.json` pair looks like a naming-variant duplicate (~31 MB combined). One should be deleted or symlinked.

## Preventive rule (runbook note)

**OPS RULE:** No binary artifacts (tar.gz, png, html dumps) belong in `memory/`. Backups go to project-root `backups/`; large reports (>1 MB JSON) should be split or archived. Any file >1 MB in memory/ triggers a size_guard alert at the next cycle boundary.

## Runbook line

What broke: 277 MB of fleet-backup tarballs left in memory/mechanic/backups/ from earlier ops cycles, inflating mirror payload and tripping size guard. What fixed it: `shutil.move` to project-root `backups/`; no restart needed; next mirror cycle will pick up the smaller tree.
