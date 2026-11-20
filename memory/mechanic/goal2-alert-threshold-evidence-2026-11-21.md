# Goal 2 - Self-Healing Mirror: Alert Threshold Test Evidence

Date: 2026-11-21
Artifact: memory/mechanic/goal2_mirror_heal_selftest.py

## What was tested
The alert threshold logic in `memory/ops/mirror_heal.py`:
- MAX_AGE_S = 900 (15 min staleness trigger)
- ALERT_THRESHOLD = 3 (alert fires when >3 failures in last hour)

## Test results: 17/17 PASS

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Fresh mirror (< 15 min) | No action, no log entry | PASS |
| 2 | Stale + 0 prior failures | repair_ok logged, no alert | PASS |
| 3 | Stale + 3 prior failures (boundary) | repair_ok, no alert (threshold is >3) | PASS |
| 4 | Stale + 4 prior failures + repair fails | repair_failed, ALERT=True, alert_msg present | PASS |
| 5 | No mirror log file | repair_failed logged | PASS |
| 6 | Stale + mirror script exits 1 | repair_failed with error detail | PASS |

## Remaining for full closure
- [ ] Register `MirrorHeal` schtask on White (15-min interval) - needs elev.py / non-sandbox seat
- [ ] Two weeks of clean production repair logs
- [ ] Zero unexplained drift > 5 min in production

## Command to run from White
```
python elev.py --shell "schtasks /create /tn MirrorHeal /tr \"python C:\\path\\to\\memory\\ops\\mirror_heal.py\" /sc minute /mo 15"
```
