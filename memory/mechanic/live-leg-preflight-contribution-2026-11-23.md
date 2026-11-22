# Mechanic team contribution: live-leg pre-flight check
Date: 2026-11-23 | Agent: Mechanic | Type: option (b) workflow improvement

## What was built
- `memory/ops/live_leg_preflight.py` (104 lines, py_compile PASS)
- `memory/ops/live-leg-preflight-2026-11-23.md` (ops doc with manual checklist + item independence table)

## Purpose
Before a non-sandbox White operator runs the 6-item live-leg runbook, this script checks all
preconditions (:8888, :8099, elev.py, COM/schtasks) and reports GO/BLOCKED per item.
Supports partial runs: items are independent (e.g., items 4+5 need only :8099; item 6 needs only COM).

## Assists
- Archivist G3 (sole open goal): makes the final step's precondition explicit and separable from the other 5 items.
- All 6 live-leg runbook items: operator knows exactly what to expect before starting.

## Evidence
- `python -m py_compile memory/ops/live_leg_preflight.py` → exit 0
- Ops INDEX.md updated with pointer line
- Script logic: checks socket ports, elev.py exit code, schtasks COM availability; per-item GO/BLOCKED + partial-run guidance