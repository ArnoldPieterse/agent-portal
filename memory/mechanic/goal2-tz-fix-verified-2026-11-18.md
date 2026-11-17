# Goal #2: TZ bug fix verified + live repair logged (2026-11-18)

## What was done
Fixed the recurring TZ bug in `memory/ops/mirror_heal.py`:
- **Root cause**: memory_mirror.py writes timestamps in LOCAL time (UTC+10 on this host) with no tz suffix. mirror_heal.py parsed them as UTC, producing negative ages (-30213s = "future") so stale detection never fired.
- **Fix**: Changed `tzinfo=datetime.timezone.utc` to `tzinfo=datetime.datetime.now().astimezone().tzinfo` (local timezone).

## Verification
- Before fix: `DRY-RUN: mirror fresh (-30213s < 900s) - no action`
- After fix: `DRY-RUN: STALE detected (5806s > 900s), would re-run mirror`
- Live run: `repair_ok` logged to mirror-repairs.jsonl (entry #4, ts=2026-11-17T23:33:45Z)

## Status toward closure
Goal requires "two weeks of clean repair logs with zero unexplained drift >5 min". Now that TZ detection works correctly, the script will properly detect and repair staleness on each 15-min cycle. Need to accumulate ~10 more days of entries.

## Runbook note
What broke: mirror_heal.py parsed local-time timestamps as UTC on non-UTC hosts → negative ages → stale detection dead. What fixed it: use `datetime.now().astimezone().tzinfo` for the tzinfo parameter. Recurs if mirror sync reverts the file - re-apply same one-line change.
