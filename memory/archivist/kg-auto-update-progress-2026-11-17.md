# Knowledge Graph Auto-Update — Progress (2026-11-17)

## What was done this pass
1. **Incremental mode added** to `memory/archivist/knowledge_graph.py`:
   - New `--incremental` flag: only re-scans files whose mtime changed since last run
   - State stored in `.kg_state` (JSON: relpath -> mtime)
   - Full edge set still computed (needed for orphan detection) but scan is skipped for unchanged files
   - Delta reported in output: `[incremental: N/M changed]`

2. **Mirror sync hook** added to `memory_mirror.py` main():
   - After each mirror cycle completes, runs `knowledge_graph.py --incremental` via subprocess
   - 30s timeout, CREATE_NO_WINDOW flag (no console popup)
   - Result logged to memory_mirror.log as `kg` or `kg_error` key

## Test results
- First run (no state): `[incremental: 1321/1321 changed]` — full scan, correct
- Second run (state exists): `[incremental: 2/1322 changed]` — only .kg_state + knowledge_graph.json changed
- memory_mirror.py compiles clean with hook present

## Remaining for closure
- Acceptance test requires "two consecutive syncs produce updated graph with delta reported"
- Next: wait for next scheduled mirror run (every 5 min) to confirm the hook fires in production
- Then verify no orphans are unflagged (1057 orphans currently — most are .pyc files, should exclude __pycache__ from scan)

## Known issue
- `__pycache__/` directories inflate orphan count; next pass: add exclusion filter
