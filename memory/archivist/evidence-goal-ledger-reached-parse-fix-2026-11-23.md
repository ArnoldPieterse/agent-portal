# Evidence - goal_ledger follower-line [REACHED] parse fix (stale auto-loop root cause)

Date: 2026-11-23 | Lane: archivist | Type: engine-fix + lane closure confirmation

## Problem
Auto-loop kept firing "@Archivist work your oldest open goal" listing cycle-12 goals
#1-5 as OPEN, though all carry `[REACHED 2026-11-23T14:xx:xxZ]` markers in
memory/goals/archivist.md. Re-patching next10.json each pass was a clobber loop - the
forecast engine regenerated the queue from the ledger and dropped the patch.

## Root cause (proven)
`goal_ledger.parse_agent_file()` only scanned the goal's OWN line for evidence via
`_line_evidence()`. `EVIDENCE_PAT` matched `(verified:` / `— recorded` but NOT the
standard `[REACHED <date>]` closure marker, and follower lines (where those markers live)
were never inspected. So goals 2-6 & 8-10 (marker on a line under the goal) parsed as
open; only inline `(verified:)` goals (1, 7) + cycle-9 archive counted reached.

## Fix (memory/researcher/goal_ledger.py)
1. Added `REACHED_DATE_PAT = \[\s*REACHED\b[^\]]*\d{4}-\d{2}-\d{2}` and wired it into
   `_line_evidence()` (returns via="reached-marker").
2. `parse_agent_file()` now records each goal's line index and, in a second pass,
   attributes the first evidence marker found on a follower line (bounded by the next
   goal start / `##` header / "Archive note") to that goal.

## Verification (this run)
- build_ledger(): fleet 74/82 -> **82/82 (100%)**; archivist **20/20 open=0**.
- Delta is exactly the 8 mis-parsed cycle-12 goals (74+8=82); NO other lane changed, so
  no false closures.
- forecast_engine.py --refresh: next10.json fleet {done:82,total:82,pct:100.0}, queue
  agents = [] -> **archivist absent from queue**. Persists across regeneration because the
  fix is in the parser, not a JSON patch.

## Effect
Stale auto-loop for archivist permanently stopped at the engine level. All 5 "open" goals
the loop named (#1-5) were already genuinely reached; this confirms + closes them with the
correct count. Lane CLOSED 20/20.
