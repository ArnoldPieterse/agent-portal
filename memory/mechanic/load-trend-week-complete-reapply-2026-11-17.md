# load_trend.py --week-complete re-applied (mirror revert #5)

Date: 2026-11-17
Agent: Mechanic

## What happened
`--week-complete` flag was reverted by mirror sync cycle (same pattern as
load_probe.py outage guard). Re-applied + verified this pass.

## Verification
- `python memory/ops/load_trend.py` -> "load_trend OK (2 days, no regression > 30%)" rc=0
- `python memory/ops/load_trend.py --week-complete` -> "2/7 days (need 5 more)" rc=1
- `--help` shows the flag

## Day-7 closure command (ready to run once >=7 entries in load-baseline.jsonl)
```
python memory/ops/load_trend.py --week-complete && python memory/researcher/goal_ledger.py --record mechanic 4 --note 'load_trend --week-complete PASS: 7 days, no regression >30%; report at memory/ops/load-week-report.json'
```

## Runbook note
Mirror cycle reverts load_probe.py and load_trend.py local edits. After each mirror sync,
re-apply both before running probes or checking week status. (5th occurrence for this pattern.)
