# Load Probe Stall Diagnostic (2026-11-22)

## Finding
`load-baseline.jsonl` has 5/7 distinct days (Nov 16-20). No entries for Nov 21 or 22 in either
`load-baseline.jsonl` OR `load-outage.jsonl`. The schtask appears to have stopped executing entirely.

## Evidence
```
$ python memory/ops/load_trend.py --week-complete
load_trend INCOMPLETE 5/7 days (have: 2026-11-16, 2026-11-17, 2026-11-18, 2026-11-19, 2026-11-20)
```

Last baseline entry: 2026-11-20 09:00:01
Last outage entry:   2026-11-17 17:17:46 (port 9 typo - early bad run)

## Root Cause Hypothesis
The schtask `PortalLoadProbe` was registered on Nov 18 and produced data through Nov 20.
After that, NO output in either file = the task didn't execute at all (not even a failed probe).
Most likely: the `python` command in the task's `/tr` path isn't resolving for SYSTEM context
on those days (PATH change, or the registered path is relative).

## Required Fix (non-sandbox White seat)
1. Check task status: `schtasks /query /tn PortalLoadProbe /v /fo LIST`
   - Look at "Last Run Time" and "Last Result" codes
2. If Last Result != 0 or Last Run is stale, fix the `/tr` to use absolute Python path:
   `schtasks /change /tn PortalLoadProbe /tr '"C:\Projects\Workspace\Python\pythoncore-3.15-64\python.exe" "Z:\memory\ops\load_probe.py --host 127.0.0.1 --port 8099"'`
3. Force one run: `schtasks /run /tn PortalLoadProbe`
4. Verify new entry appears in load-baseline.jsonl
5. Re-run `python memory/ops/load_trend.py --week-complete` for closure verdict

## Closure Path
Once 7/7 days are present, `--week-complete` emits WEEK_COMPLETE + trend verdict.
Then: `python memory/researcher/goal_ledger.py --record mechanic 1 --note 'load_trend --week-complete PASS; evidence: load-trend-report.json'`
