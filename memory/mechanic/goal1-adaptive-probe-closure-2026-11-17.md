# Goal #1 Closure: Adaptive Fleet Probe v2 — Latency Drift + Process Anomaly Verified
Date: 2026-11-17 (Mechanic)
Status: ACCEPTANCE TEST PASSED

## Acceptance criterion
"Verified: simulating a degrading host -> severity escalates over N runs."

## Evidence
- `memory/mechanic/fleet_probe_v2_test.py` — 11/11 tests pass
- Key test `test_latency_escalation_simulation`: baseline 5ms, latency sequence [5,7,12,20]ms
  produces severities [OK, OK, WARN, CRIT] — escalation confirmed over consecutive runs.
- Process-count anomaly: `classify_proc` correctly classifies +35% as WARN, +150%/+300% as CRIT,
  -40% drop as WARN (symmetric detection).
- Adaptive scheduling: `adaptive_interval` returns 2min/CRIT, 5min/WARN, 10min/OK.

## What's built (on disk)
- `memory/ops/fleet_probe_v2.py` — full probe with TCP latency + process-count anomaly + adaptive cadence
- `memory/mechanic/fleet_probe_v2_test.py` — unit tests (11 cases, all pass)
- History: `memory/ops/fleet-probe-history.jsonl` (append-only, feeds baseline computation)

## Remaining for production deployment (non-blocking for closure)
- 3+ consecutive runs from a non-sandbox seat with full LAN access (sandbox produces false CRITs
  due to firewall; logic verified by unit tests)
- Scheduled task wiring (adaptive cadence: next_interval_min field in each run record)

## Runbook note
Sandbox network restrictions produce false CRITs on remote hosts. The probe logic is correct —
unit tests prove the escalation model works. Deploy from a LAN-connected seat for clean baselines.
