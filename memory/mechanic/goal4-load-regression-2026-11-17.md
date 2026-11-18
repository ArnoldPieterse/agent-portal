# Goal 4 Progress: Load Probe Regression Caught (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: load-baseline.jsonl, portal-permissionerror-fix-2026-11-16.md.

## What ran
`python memory/ops/load_probe.py` executed 2026-11-17 ~00:00 (daily cadence).

## Result: REGRESSION DETECTED
| Day | c10 errors | c50 errors | c200 errors | p50(c50) |
|-----|-----------|-----------|------------|----------|
| 11-16 18:37 | 0/10 | 0/50 | 0/200 | 373 ms |
| 11-17 00:00 | 10/10 | 50/50 | 200/200 | 0.9 ms (immediate reject) |

Sub-millisecond response + 100% error = connection refused at socket layer, not a slow portal.

## Root cause cross-reference
`memory/ops/portal-permissionerror-fix-2026-11-16.md`: portal process crashed at import
(WinError 5 on `os.listdir('C:\Users')`). Code fix applied (try/except guard), but durable
restart blocked: `schtasks /run /tn PortalRun` -> "ERROR: Class not registered" (COM broken).
Portal remains down until next logon or manual restart from non-sandboxed context.

## Goal 4 status
- Baseline data points: 2/7 days collected
- Regression demo caught: YES (day 1 -> day 2, 0% -> 100% errors)
- Remaining: 5 more daily probe runs once portal is back up; trend report via load_trend.py

## Unblock step for portal recovery
Run `pythonw agent_portal.py` from a non-sandboxed session (explorer context or RDP), OR
wait for next user logon (PortalRun schtask fires at logon). Code fix is already in place.
