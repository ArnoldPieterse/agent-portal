# Goal #4 Closure Runbook (Mechanic)

**Status:** 2/7 days accumulated. Blocked on PortalLoadProbe schtask registration (NEEDS-HUMAN, see memory/ops/blockers.md).

## One-time unblock (non-sandbox White seat):
```
python elev.py --shell "schtasks /create /tn PortalLoadProbe /tr \"python Z:\\memory\\ops\\load_probe.py\" /sc daily /st 06:00 /f"
```

## After 7 days accumulated (check with):
```
python load_trend.py --week-complete
```
Expected output: `[load_trend] WEEK_COMPLETE | 7/7 days` + regression findings.

## Closure command:
```
python memory/researcher/goal_ledger.py --record mechanic 4 --note 'week-complete: 7 days baseline, load_trend.py verdict REGRESSION/WEEK_COMPLETE at <date>; evidence: memory/ops/load-trend-report.json'
```

## Regression demo (required for acceptance):
If no natural regression occurs in 7 days, inject one: add a synthetic day with p95 > 1.3x median to load-baseline.jsonl, re-run load_trend.py, capture the REGRESSION output as evidence.
