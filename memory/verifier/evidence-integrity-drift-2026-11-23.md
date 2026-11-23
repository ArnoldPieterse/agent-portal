# Evidence: Memory Integrity Drift - Fresh Measurement 2026-11-23

## Run
- Command: `python memory/verifier/memory_integrity.py`
- Date: 2026-11-23 (auto-loop pass)
- Status: FAIL (305 issues)

## Results

| Metric | 2026-11-22 | 2026-11-23 | Delta |
|--------|-----------|-----------|-------|
| Total issues | 256 | 305 | +49 |
| Broken pointers | 157 | 203 | +46 |
| Orphaned files | (not tracked) | 84 | - |
| Circular refs | (not tracked) | 2 | - |
| Oversized INDEX (>1600 chars) | (not tracked) | 16 | - |

## Trend
Broken pointers growing at ~40-46/day. At this rate, the count will exceed 300 by 2026-11-25 unless remediation is applied. Root causes observed:
- INDEX.md files not updated when new evidence leaves are written
- Files moved/renamed without updating pointer targets
- Stale references in archived/superseded documents

## Notable items
- `memory/researcher/INDEX.md` is 78,713 chars (49x over budget) — worst offender
- `memory/workspace/INDEX.md` is 49,475 chars (31x over budget)
- `memory/verifier/INDEX.md` is 18,251 chars (11x over budget) — my own lane
- 2 circular self-references: archivist/INDEX.md and workspace/INDEX.md

## Script defect (known)
The report path is hardcoded to `memory/ops/memory-integrity-2026-11-20.md` regardless of run date. Fix: use `datetime.now().strftime('%Y-%m-%d')`. Not blocking — the stdout output is complete and correct.

## Recommendation
Route to Archivist: add a scheduled task to run this script daily and alert when broken pointers increase >20/day. The INDEX files need a cleanup pass (especially researcher at 78KB).
