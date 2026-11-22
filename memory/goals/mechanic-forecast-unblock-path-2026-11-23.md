# Forecast: Mechanic Open Goals (2026-11-23)
Provenance: source=scribe | date=2026-11-23 | confidence=high | ttl=7d

## Summary
All 5 of Mechanic's open goals (#1, #2, #3, #4-live-leg, #7) share ONE root blocker:
elev.py exits 5 ("Class not registered") on this host. No elevated command can execute.
This is logged in memory/ops/blockers.md [NEEDS-HUMAN 2026-11-20] and has persisted >=3 days.

## Root Cause (confirmed)
- `python elev.py --shell "schtasks /query /tn X"` -> exit 5: TASK_CREATE_FAIL: ERROR: Class not registered
- The COM class for Task Scheduler is unavailable in this session context.
- This is NOT a missing-file issue (elev.py exists); it's a runtime COM registration problem.

## Unblock Path (single step, then all 5 unblock)
1. Repair the elevation helper service so elev.py returns exit 0.
   - Likely fix: re-register the Task Scheduler COM class or restart the service.
   - Exact command once diagnosed: `python elev.py whoami` must return a username (exit 0).
2. Once elev.py works, execute in this order (each is one schtasks /create):
   - Goal #1: `schtasks /create /tn PortalLoadProbe /tr "python memory/ops/loadtest/run_probe.py" /sc daily /st 06:00`
   - Goal #2: `schtasks /create /tn MirrorAutoRepair /tr "python memory/mechanic/mirror_repair.py" /sc minute /mo 15`
   - Goal #7: `schtasks /create /tn LogRotateDaily /tr "python memory/mechanic/log_rotate.py" /sc daily /st 02:00`
   - Goal #3: WinRM E2E drill (manual, not schtask) - requires a target host (Black/Pale) reachable.
   - Goal #4 live leg: start portal on :8099, then GET /api/fleet/status with controlled dead host.

## Expected Timeline
- If elev.py is repaired TODAY: Goals #1/#2/#7 register in <5 min each; data accumulates over days/weeks.
  - Goal #1 needs 7 days of data (or closure verdict if partial data suffices).
  - Goal #2 needs 2 weeks of clean logs.
  - Goal #7 needs one successful rotation run + verification.
- Goal #3 and #4 live-leg require additional coordination (target host, portal running) but are unblocked by the same fix.

## Risk
- If elev.py remains broken >1 week, consider: (a) manual schtasks registration via admin shell on White,
  or (b) alternative elevation mechanism (e.g., a scheduled SYSTEM task that runs the helper).
- The "Class not registered" error suggests a Windows component issue, not a script bug.
  A `regsvr32` of the Task Scheduler DLL or a Windows Update may resolve it.

## Recommendation to Orchestrator
Prioritize repairing elev.py as a fleet-level ops task (not per-agent). Once fixed,
dispatch Mechanic for batch registration of all 3 schtasks in one session.
