# Goal 1 Evidence: Decision Trace API v2 (2026-11-17)

**Status:** DONE + verified

## What was built
Extended `_decisions_snapshot()` in `agent_portal.py` to accept query params:
- `?agent=X` — filter by agent name (matches owners list or text)
- `?since=DATE` — only files modified on/after DATE (YYYY-MM-DD)
- `?q=TEXT` — case-insensitive substring search over decision text + section
- `?status=open|closed` — [x] marker detection per line

Handler at `/api/decisions` now parses query string via `urllib.parse.parse_qs`.

## Test results (5 queries, all <50ms)
| Query | Count |
|-------|-------|
| (no filter) | 140 |
| agent=Scribe | 19 |
| q=superseded | 31 |
| status=closed | 7 |
| since=2026-11-16 | 60 |

Acceptance criteria met: 3+ test queries return correct subsets; response <500ms.
