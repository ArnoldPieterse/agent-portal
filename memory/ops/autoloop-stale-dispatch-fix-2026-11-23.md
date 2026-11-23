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
