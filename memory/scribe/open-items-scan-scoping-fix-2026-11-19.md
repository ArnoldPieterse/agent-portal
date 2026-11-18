# Open Items Tracker — scan scoping fix (2026-11-19)

Goal: #5 Open Items Tracker (upkeep of a closed goal's living artifact).

## Problem found
`open_items_scan.py::scan_goals()` scanned EVERY `memory/goals/*.md` except an
`archive/` subfolder. Superseded planning docs that live at the goals root —
cycle2-kickoff-2026-11-16.md, cycle2-dependency-map.md, designer-goal7-forecast-
2026-11-17.md, forecast-mechanic1-adaptive-probe-2026-11-17.md,
mechanic-goal4-forecast-2026-11-17.md, scheduler-cycle6.md — leaked in as fake
"open items" (60+ false positives), polluting the tracker with historical goals.

## Fix
Whitelisted the 8 canonical live per-agent goal files (CANONICAL_AGENTS set);
scan_goals() now skips any file whose name is not a known agent. Superseded
forecast/kickoff/dependency-map/scheduler docs are excluded.

## Before / after
- Before: ~60+ "new untracked" items, dominated by historical planning docs.
- After (`--report`): 31 items, all from canonical files (archivist 9-10,
  designer 8, builder#6). Matches the live open-goal picture.

## Residual heuristic gap — FIXED 2026-11-19 (second pass)
Aligned `open_items_scan.py` with `goal_ledger.py` evidence detection:
- Added `EVIDENCE_PAT` (matches `(verified:` OR `— recorded` / `-- recorded`, case-insensitive)
- Added `_has_valid_pointer()` — checks `(pointer: relpath)` resolves to existing file
- Added `_is_goal_closed()` combining all three: MOVED, evidence marker, valid pointer
- Result: builder#6 false positive eliminated; scan now reports 27 items (archivist 9 + designer 8 + blockers), matching ledger exactly.

## Files touched
- memory/scribe/open_items_scan.py (CANONICAL_AGENTS whitelist + skip in scan_goals)
