# Decision Trace API v2 - Evidence (2026-11-17)

## What was done
Extended `_decisions_snapshot()` in `agent_portal.py` with 4 query params:
- `?agent=X` - filter by detected owner name (case-insensitive)
- `?since=YYYY-MM-DD` - filter by file mtime >= date
- `?status=open|done|closed` - filter by inferred status (heuristic: closed > done > open)
- `?q=text` - full-text search over decision text + section heading

Added `"status"` field to each result. Status inference:
- **closed**: line contains superseded/reverted/voided/withdrawn
- **done**: line contains done/completed/shipped/landed
- **open**: default

## Test results (2026-11-17)
| Query | Count | Expected |
|-------|-------|----------|
| (no filter) | 134 | all decisions |
| status=open | 92 | subset of 134 [PASS] |
| status=done | 9 | subset of 134 [PASS] |
| status=closed | 33 | subset of 134 [PASS] |
| agent=Scribe | 19 | only lines mentioning Scribe [PASS] |
| since=2026-11-16 | 54 | only files modified on/after that date [PASS] |
| q=round | 33 | full-text match [PASS] |

All subsets are proper subsets of the unfiltered set. Response time <1ms (in-process).

## Files changed
- `agent_portal.py`: `_decisions_snapshot()` signature + body; route handler passes query params

## Acceptance criteria met
- [x] 3 test queries return correct subsets (6 tested)
- [x] Response <500ms on current data volume (134 decisions, in-process <1ms)
