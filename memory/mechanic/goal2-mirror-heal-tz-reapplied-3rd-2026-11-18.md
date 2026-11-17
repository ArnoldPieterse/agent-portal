# Goal #2 - mirror_heal.py TZ fix re-applied (3rd time) 2026-11-18

Date: 2026-11-18 ~auto-loop pass
Agent: Mechanic

## What happened
Mirror sync reverted the TZ fix in memory/ops/mirror_heal.py `_last_sync_time()` for the 3rd time.
Detected via test suite (test_mirror_heal_tz.py): 4/6 FAIL with negative ages (~-35700s offset).

## Fix applied
Same diff as before:
- Old: `.replace(tzinfo=datetime.timezone.utc)` (misreads local ts as UTC)
- New: `.astimezone().astimezone(datetime.timezone.utc)` (local -> UTC correctly)

## Verification
`python memory/mechanic/test_mirror_heal_tz.py` -> 6/6 PASS

## Root cause (unchanged)
Mirror sync overwrites memory/ops/mirror_heal.py with a copy that lacks the fix.
The test file (test_mirror_heal_tz.py) guards against silent regression but does NOT prevent it.
True fix requires either: (a) adding the fixed version to the mirror source-of-truth, or
(b) making the mirror skip this file. Both require White persistent host access.

## Remaining for goal #2 closure
- schtask registration on White (NEEDS-HUMAN: no elev.py at Red sandbox seat)
- 2 weeks of clean repair logs with zero unexplained drift >5 min
- Prevent further reverts (fix the mirror source, not just the destination)

## Runbook note
Mirror sync reverts local edits to memory/ops/mirror_heal.py. After each mirror cycle,
run `python memory/mechanic/test_mirror_heal_tz.py` to verify TZ fix is intact.
If T3 fails, re-apply: replace `.replace(tzinfo=datetime.timezone.utc)` with
`.astimezone().astimezone(datetime.timezone.utc)` in `_last_sync_time()`.