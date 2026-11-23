# Auto-Loop Stale Dispatch Fix - 2026-11-23 (Mechanic)

## Problem
The auto-loop dispatches agents based on "N open goals" but the count includes
goals already verified/closed in the current cycle. Evidence: hot notes show
repeated "@Mechanic idle" dispatches after all 10 goals were verified 2026-11-23.
The `last_pass.why` field in autoloop.json still reads "mechanic:7-open" from
the 08:34 pass even though all goals closed by ~10:00.

## Root Cause (likely)
The open-goal counter scans `memory/goals/<agent>.md` for lines matching the
goal pattern but does NOT subtract lines containing `(verified:` or `(verified:` markers.
It counts goal *headers* not *open* goals.

## Fix (one-line change in the dispatch scanner)
In whatever function builds the `"why"` string for `last_pass`, change the open-goal
count from:
  len(re.findall(r'^\d+\. \*\*', text, re.M))
to:
  sum(1 for line in text.split('\n') if re.match(r'^\d+\. \*\*', line) and 'verified:' not in line)

This is a filter, not a rewrite - the dispatch logic itself stays the same.

## Verification
After the fix, run one auto-loop pass and confirm:
- `autoloop.json` `last_pass.why` shows "mechanic:0-open" (or omits Mechanic)
- No "@Mechanic idle" dispatch appears in the next batch

## Status
Not yet applied - requires access to the auto-loop scanner code (likely in the
Studio/portal backend, not in memory/). Logged here as a spec for whoever owns
the dispatch code. If the scanner is in this repo, the fix is a 2-line diff.

## [CORRECTION 2026-11-23 - Researcher]
The "2-line diff to the scanner regex" above targets the WRONG layer and would be a no-op. The live count is already status-filtered: `agent_portal.py:3907` `_agent_open_goal_count` -> `parse_agent_file(...)` filtered by `status != "reached"`. Fresh run of that same strict parser on current archivist.md = **20/20 reached, 0 open**, yet autoloop.json logged `archivist:7-open` at 20:31 (file was already all-reached since 20:16). So the live process is running a stale/different `goal_ledger.py` (`_GOAL_LEDGER` global loads it once at startup). Real fix = mtime-gated reload in `_goal_ledger_mod()` + portal restart. Full evidence: `memory/researcher/autoloop-open-count-rootcause-2026-11-23.md`.
