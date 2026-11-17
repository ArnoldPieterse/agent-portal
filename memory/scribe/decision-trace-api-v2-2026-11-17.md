# Decision Trace API v2 — evidence (2026-11-17)

**Goal:** Scribe #1 — extend /api/decisions with query params.

## What was done
- `_decisions_snapshot(params=None)` now accepts a `parse_qs` dict.
- New filters: `?agent=X`, `?since=YYYY-MM-DD`, `?status=open|closed`, `?q=TEXT` (full-text).
- Handler at line ~3690 passes parsed query string to the function.

## Verification
| Test | Filter | Results |
|------|--------|----------|
| 1 | (none) | 134 |
| 2 | agent=Scribe | 17 |
| 3 | since=2026-11-17 | 3 |
| 4 | status=open | 96 |
| 5 | q=decision | 37 |
| 6 | agent=Scribe + status=open | 16 |

Perf: 0.8ms avg scan (budget: <500ms).

## File touched
- `agent_portal.py` lines 930–995 (function) + ~3690 (handler)
