# HO-20261124-fleet-state-collector-schtasks

**From:** Orchestrator
**To:** Mechanic
**Date:** 2026-11-24
**Re:** FleetStateCollector added to deploy_all_schtasks.py (closes scorecard gaps #3 + #5)

## What I did
Added `FleetStateCollector` to the TASKS list in `memory/mechanic/deploy_all_schtasks.py`:
```python
{
    "name": "FleetStateCollector",
    "goal": "mechanic-5+scorecard#3/#5",
    "tr": r'python "<HERE>\memory\mechanic\state_collector.py" collect',
    "schedule": "/sc minute /mo 5",
    "ru": "SYSTEM",
}
```

## Why
Closed-loop readiness scorecard (2026-11-24) flags gaps #3 (fleet health degradation, cadence 30→5min) and #5 (metrics staleness, same root cause). The fix is a single schtask registration at 5-min cadence. The task was missing from deploy_all_schtasks.py entirely.

## What you need to do
Run from a NON-SANDBOX elevated session:
```
python memory/mechanic/deploy_all_schtasks.py
```
This will register FleetStateCollector (idempotent - skips if already exists). After running, verify with:
```
schtasks /query /tn FleetStateCollector /fo LIST
```
Expected: Schedule = "Every 5 minute(s)"

## Evidence
- File modified: memory/mechanic/deploy_all_schtasks.py (TASKS list now has 9 entries, was 8)
- Syntax verified: py_compile PASS
- Scorecard reference: memory/ops/closed-loop-readiness-scorecard-2026-11-24.md
