# Goal 2 - Mirror Heal Timezone Fix (2026-11-21)

## Problem
`mirror_heal.py` parsed `memory_mirror.log` timestamps as UTC (`.replace(tzinfo=utc)`),
but `memory_mirror.py` writes them via `datetime.datetime.now()` (naive local time).
On any non-UTC host, the age calculation was wrong:
- On UTC+10 (Red): log showed 23:30 local, script treated as 23:30 UTC, compared to 16:27 UTC now
  → negative age (-25408s) → reported "fresh" when actually ~3h stale

## Fix (3 changes to memory/ops/mirror_heal.py)
1. `_now()`: changed from `datetime.now(utc)` to `datetime.now()` (naive local)
2. `_last_sync_time()`: removed `.replace(tzinfo=utc)` — parse as naive local
3. `_recent_failures()`: cutoff format uses `.strftime("%Y-%m-%dT%H:%M:%S")` for consistency

## Verification
- Before fix: `DRY-RUN: mirror fresh (-25408s < 900s) - no action` (WRONG — should be stale)
- After fix:  `DRY-RUN: STALE detected (10617s > 900s), would re-run mirror` (CORRECT)

## Remaining for full closure
- [ ] Register schtask on White: `python memory/ops/register_mirror_heal_task.py`
      (requires non-sandbox seat; COM class not available in this sandbox)
- [ ] Two weeks of clean repair logs
- [ ] Alert threshold test (simulate 4 failures → alert fires)

## Status: IN PROGRESS (tz bug fixed, schtask registration pending White access)