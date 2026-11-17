# Mirror-Revert Deep-Dive — Day-7 Closure Runbook (goal #3)

Pre-staged 2026-11-17 so closure is ONE command once the live window (11-17→11-24) fills.
Status: pipeline proven, instrumentation live, parse validated. Only LIVE data remains.

## State at pre-stage time (measured 2026-11-17)
- `mirror_events.log` (Z:\) contains ONLY `_test` lines from the self-test run at 20:53:18.
- No live mirror cycle has executed since instrumentation landed -> zero live events on day 1 (expected; window still open).
- This is NOT a blocker recurrence — the NEEDS-HUMAN entry in memory/ops/blockers.md already covers seeding the live mirror at C:\Projects\Workspace. Do not re-probe.

## Prerequisite (one-time, Mechanic-owned)
Live mirror must run against C:\Projects\Workspace so real push/pull/revert events append to Z:\mirror_events.log.
Blocker (already logged, do NOT re-probe): seed one manual live mirror run; confirm schedule.

## Day-7 closure commands (run ~2026-11-24)
```python
# 1. Parse the live log into the frequency table
from importlib import import_module
import sys, os
sys.path.insert(0, r"Z:")
m = import_module("parse_mirror_events") if False else None
# canonical: run from working dir
```
```cmd
python memory/researcher/parse_mirror_events.py Z:\mirror_events.log
```
Expected output shape (all hand-verified in pipeline validation):
- live event count (skips any `_test` lines)
- counts by kind (write/revert), by dir (push_root/push_mem/pull_mem), by path, by trigger, by hour

## Analysis leaf to write at day 7 (this file's sibling)
`memory/researcher/mirror-revert-analysis-2026-11-24.md` must contain:
1. Frequency table: which files revert most + what triggers them (pin_drift vs other).
2. Top-3 reverting paths with event counts.
3. 2-3 targeted fixes BEYOND the auto-repair daemon (e.g. pin-stability guard, per-file epoch stamping from goal #1 spec, write-ordering fix).
4. Confidence + any residual uncertainty.

## Closure record
`python memory/researcher/goal_ledger.py --record researcher 3 --note '<one-week live dataset analyzed; artifact path>'`

Acceptance: one-week data set + analysis leaf with concrete fix recommendations (matches goal #3 verified clause).
