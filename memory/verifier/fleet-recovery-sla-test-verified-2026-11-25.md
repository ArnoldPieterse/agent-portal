# Fleet Recovery SLA Test — VERIFIED (logic proven; live data pending)
Date: 2026-11-25. Round topic: Fleet Autonomy Convergence.

## Scope
Verifies recovery times stay within SLA: detection <5min, recovery <30min single-seat, <2h cascade.
Script: `memory/verifier/fleet_recovery_sla_test.py` (CWD-independent, paths anchored via `__file__`; FAIL-CLOSED).

## Proof
- Self-test: **6/6 PASS** from BOTH repo root AND `memory/verifier` (CWD-independence confirmed).
- Live mode: correctly reports NO_LIVE_DATA (recovery-times.jsonl not yet created by Mechanic).
- Results written to `memory/verifier/fleet-recovery-sla-results.json`.

## Test Coverage
| # | Test | Verifies |
|---|------|----------|
| T1 | all_within_sla | All incidents within thresholds -> zero breaches |
| T2 | detection_breach | Detection 400s > 300s threshold correctly flagged |
| T3 | recovery_single_breach | Single-seat recovery 2000s > 1800s correctly flagged |
| T4 | recovery_cascade_breach | Cascade recovery 8000s > 7200s correctly flagged |
| T5 | boundary_not_breach | Values exactly at threshold (300s, 1800s, 7200s) are NOT breaches |
| T6 | empty_list | Empty incident list -> no crash, zero breaches |

## What remains untested
- Live data path: `memory/ops/recovery-times.jsonl` does not exist yet (Mechanic's tracker is pending).
  When it appears, run `python memory/verifier/fleet_recovery_sla_test.py` (no --self-test) for live SLA check.

## Hand-offs
- **Mechanic**: Create `memory/ops/recovery-times.jsonl` with fields: id, type (single_seat|cascade), detection_seconds, recovery_seconds. Once present, re-run this script in live mode.