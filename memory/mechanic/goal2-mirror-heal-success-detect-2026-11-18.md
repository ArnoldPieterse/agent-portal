# Goal #2 - mirror_heal.py success-detection fix (2026-11-18)

Date: 2026-11-18 ~07:xx
Agent: Mechanic

## Bug found and fixed
`_last_sync_time()` was checking if the mirror script RAN recently, not if it SUCCEEDED.
With all hosts failing SMB auth (System error 5), the heal saw "fresh" timestamps and never triggered repair - blind to persistent failure.

## Fix applied to memory/ops/mirror_heal.py
1. **Success detection**: `_last_sync_time()` now only returns a timestamp if at least one host in `results` has NO `error` key. All-failed runs are skipped.
2. **TZ fix re-applied** (3rd occurrence): `.replace(tzinfo=utc)` -> `.astimezone().astimezone(utc)`
3. **Message clarity**: "no mirror log found" -> "no successful sync found in log (all runs failed or log missing)"

## Verification
- `python memory/mechanic/test_mirror_heal_tz.py` -> 6/6 PASS (updated test entries to use realistic results format)
- `python memory/ops/mirror_heal.py --dry-run` -> correctly reports "no successful sync found" (was: "mirror fresh (4s < 900s)" before fix)
- Manual trace: all 7 log entries have either no results or all-host errors -> _last_sync_time() returns None -> repair triggers

## Impact
Once registered as schtask on White, the heal will correctly detect that syncs are failing and attempt repair (re-run memory_mirror.py). Without this fix, it would silently do nothing while all hosts stay out of sync.

## Remaining for closure
- Schtask registration on White (NEEDS-HUMAN: non-sandbox seat)
- Two weeks of clean repair logs with zero unexplained drift >5 min

## Runbook note
Mirror sync reverts local edits to memory/ops/mirror_heal.py. After each mirror cycle, run:
`python memory/mechanic/test_mirror_heal_tz.py` to verify both TZ fix AND success-detection are in place.
If any test fails, re-apply the fix (see this file for the exact changes).
