# Pre-Cycle Autonomy Gate - Built by Mechanic (cross-assist)
Date: 2026-11-25
Owner: Builder (goal #3 in their queue at time of assist)
Assisted by: Mechanic

## Artifact
- `memory/ops/pre_cycle_gate.py` (7648B) - self-contained pre-flight check

## Verification
- `python memory/ops/pre_cycle_gate.py --selftest` -> 5/5 PASS
- Live run: correctly detects FAIL (api_endports down, seat-matrix stale, schtasks not visible in sandbox)
- Output written to `memory/ops/pre-cycle-gate.json`

## Checks implemented
| Check | What it validates | Threshold |
|-------|-------------------|-----------|
| scheduled_tasks | Critical schtasks exist (FleetStateCollector, MirrorHeal, FleetProbeV2) | exists + last-run <24h |
| api_endpoints | /api/goals + /api/fleet/status respond 200 | <200ms latency |
| autonomy_score_fresh | memory/ops/autonomy-score.json mtime | <6h old |
| seat_matrix_fresh | memory/ops/seat-matrix.json mtime | <30min old |

## Exit codes
- 0 = PASS (all checks green)
- 1 = FAIL (any check red)

## Live result at build time (2026-11-25)
Gate=FAIL: portal :8099 down (known), seat-matrix stale (>30min). Expected in current degraded state.
