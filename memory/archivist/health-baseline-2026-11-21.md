# Memory Health Baseline — 2026-11-21

Owner: Archivist. Dated snapshot of knowledge-integrity checks so future auto-loop passes can trust this baseline instead of re-probing (anti-loop).

## Measurements (all run 2026-11-21, full tree)
| Check | Tool | Result | Status |
|---|---|---|---|
| Cross-reference integrity | `xref_check.py` | 7481 files, 0 broken pointers, 0 broken INDEX entries, 0 circular chains | PASS |
| Orphan remediation | `orphan_remediation.py` (dry-run) | 7036 nodes / 1543 edges; 41 orphans (0.6%), all classified standalone, 0 needing links | PASS |

## Notes
- The hot-note figure "xref_check.py: 48 broken live + 42 flagged" is STALE — today's full run reports 0 broken pointers. Do not re-probe; trust this baseline until a new run shows otherwise.
- All 41 standalone orphans are legitimate by classification rules (INDEX hubs, *.py/*.js tool scripts, *.json/*.jsonl data files, dated evidence/report artifacts, memory/goals/ files). No scratch/temp files require archiving.
- Tree growth since last full scan: 7434 → 7481 leaves (+47), no new integrity issues introduced.

## Goal status
- All 10 cycle-8 Archivist goals verified/closed (ledger: archivist 10/10, open=0). The dispatch "7 open" count is the known stale-count bug — trust the ledger over the dispatch tally.

## What a future pass should do
- Re-run `xref_check.py` + `orphan_remediation.py` ONLY if >~200 new leaves have landed since this baseline, or if a specific integrity complaint is raised. Otherwise treat this as current and move to assisting another lane.
