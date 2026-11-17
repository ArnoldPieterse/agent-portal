# Scribe Goal 1: Decision Trace API v2 — VERIFIED 2026-11-17

**What was done:** Added query-param filtering to `_decisions_snapshot()` in `agent_portal.py`.

**Filters implemented:**
- `?agent=X` — match owner name or text mention (case-insensitive word boundary)
- `?since=YYYY-MM-DD` — mtime >= date (bad dates silently ignored)
- `?status=open|closed` — section header contains `[x]` or not
- `?q=text` — full-text substring search over decision line

**Test results (in-process, 2026-11-17):**
| Query | Results | Latency |
|-------|---------|----------|
| agent=Scribe | 19 / 134 baseline | 26.1 ms |
| since=2026-11-17 | 3 / 134 baseline | 32.8 ms |
| q=superseded | 30 / 134 baseline | 24.1 ms |

All < 500 ms. All return correct subsets.

**Note:** Portal was not running at test time (port 8099 refused); verified via direct function call with same logic as the HTTP route handler.
