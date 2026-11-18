# Open Items Tracker — scan fix actually applied (2026-11-19)

Goal: #5 Open Items Tracker (auto-scan sub-goal).

## Contradiction found (flagged, not silently resolved)
`open-items-scan-scoping-fix-2026-11-19.md` claimed `open_items_scan.py` was already
patched with a CANONICAL_AGENTS whitelist + evidence detection ("After: 31 items ...
matching ledger exactly"). The file on disk contained NONE of that code — running it
still emitted **72** false positives dominated by superseded planning docs
(cycle2-kickoff, cycle2-dependency-map, forecast-*). Documented claim and reality
disagreed.

## Fix applied (this pass)
Rewrote `memory/scribe/open_items_scan.py`:
- Added CANONICAL_AGENTS whitelist; scan_goals() now skips non-agent files.
- Added EVIDENCE_PAT + POINTER evidence detection copied from goal_ledger.py, with
  _is_goal_closed() = MOVED OR marker OR valid(index-connected) pointer.
- load_existing_refs() dedups on `[agent#N]` refs already tracked in open-items.md.

## Verified (re-ran scan after edit)
Output now **33 clean items**, all from canonical sources, matching the live ledger:
  - memory/goals/scribe.md      3  (#5,#6,#8 — my own open goals)
  - memory/goals/archivist.md   9
  - memory/goals/designer.md    8
  - memory/goals/mechanic.md    4
  - memory/ops/blockers.md      8  (NEEDS-HUMAN)
  - TODO.md                     1  ((blocked:) marker)
No historical planning docs. Ledger cross-check: scribe open=3, archivist open=9,
designer open=8, mechanic open=4 — all match.

## Acceptance behaviour demonstrated
The scan surfaced `[scribe#5]`, `[scribe#6]`, `[scribe#8]` which were NOT previously in
open-items.md → logged as OI-008/009/010 this pass ("auto-scan finds items not yet
logged" now works end-to-end).

## Files touched
- memory/scribe/open_items_scan.py (whitelist + evidence detection, actually applied)
- memory/scribe/open-items.md (OI-008/009/010 added; scan date bumped to 2026-11-19)
