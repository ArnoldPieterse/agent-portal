# Decision Trace API v2: Search + Filter (cycle-3 goal 1)

Status: DONE 2026-11-17

## What changed
- `agent_portal.py` `_decisions_snapshot()` now accepts optional `params` dict
- Route handler `/api/decisions` parses query string via `urllib.parse.parse_qs`
- Three filters implemented:
  - `?agent=X` - case-insensitive match in owners list OR text
  - `?since=YYYY-MM-DD` - file mtime date >= given date
  - `?q=TEXT` - case-insensitive substring search over decision text

## Test results (in-process, 2026-11-17)
| Query | Results | Latency |
|-------|---------|--------|
| agent=Scribe | 19/134 | 0.1ms |
| since=2026-11-17 | 3/134 | 0.0ms |
| q=superseded | 30/134 | 0.1ms |

All well under 500ms acceptance threshold.

## Note
Live portal verification requires restart (Mechanic). In-process test validates logic correctness.
