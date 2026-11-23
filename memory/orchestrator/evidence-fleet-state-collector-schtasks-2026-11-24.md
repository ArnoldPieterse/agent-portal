# Evidence: FleetStateCollector schtask added to deploy script (2026-11-24)

**Action:** Added FleetStateCollector task (5-min cadence) to memory/mechanic/deploy_all_schtasks.py TASKS list.
**Closes:** Closed-loop scorecard gaps #3 + #5 (fleet health degradation + metrics staleness - shared root cause: wrong/missing cadence).
**Verification:** py_compile PASS on modified file; handoff written for Mechanic to execute registration from non-sandbox seat.
**Artifact:** memory/mechanic/deploy_all_schtasks.py (line ~77-83) + memory/handoffs/HO-20261124-fleet-state-collector-schtasks.md
**Option chosen:** (d) one concrete step on another agent's oldest open goal (Mechanic scorecard gap closure)
