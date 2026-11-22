# Cycle Narrative Ledger Fix (2026-11-21)

**Problem:** `cycle_narrative.py` counted raw `verified:` markers in goal files, producing 80/80 (100%) when the ledger showed 73/80 (91%). Carry-forward sections and re-run notes inflated the count.

**Fix:** `get_goal_completion()` now reads from `memory/researcher/goal_ledger_current.json` (SSOT) first; falls back to file-parsing only if the ledger is missing or corrupt.

**Verified:** dry-run for cycle 8 now reports "73 verified (91%)" matching the ledger. Fallback path unchanged for resilience.

**Owner:** Scribe (team contribution, all own goals already closed)
