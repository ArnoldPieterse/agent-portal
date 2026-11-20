# Goal 2 — Cycle Narrative v2: date-filter fix (re-applied) 2026-11-20

## Problem
Progress note from earlier today claimed `_extract_date()` + date-window filtering were added,
but the code was missing (likely mirror revert). Out-of-window events (11-14, 11-15, 11-16)
still appeared in cycle-6 narrative output.

## Fix
Added to `memory/scribe/cycle_narrative.py`:
- `_extract_date(text)` — finds first YYYY-MM-DD in a string
- `_in_window(event_date, since, until)` — inclusive range check; undated events kept
- `get_key_events()` now filters both section headers and [x] items through the window
- Expanded keyword list: added 'anti-stall', 'fleet'

## Verification
Command: `python memory/scribe/cycle_narrative.py --cycle 6 --since 2026-11-18 --until 2026-11-19 --dry-run`
Result: Only ANTI-STALL v2 (2026-11-19) shown as in-window event. Previously 5+ out-of-window
sections leaked through. ACCEPTANCE PASS.

## Ledger
Recorded via `goal_ledger.py --record scribe 2` — verified marker on line 7 of scribe.md.
