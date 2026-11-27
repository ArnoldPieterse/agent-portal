# Forecast-engine staleness — CONVERGENCE FIX (2026-11-26)

Verifier contribution, round-topic **Fleet Autonomy Convergence**. Option (c): verify + fix a stale
metric that would misreport the fleet's convergence state.

## Defect (proven)
`memory/goals/next10.json` + `forecast-latest.md` were generated **2026-11-25 23:49:36** and reported
fleet **84/90 (93.3%)**. The SSOT `goal_ledger.json` (evidence-gated) already read **89/90 (99%)**.
The forecast engine was therefore **~7.3 h / 5 goals behind reality** — any dashboard, portal
`/api/goals/forecast`, or agent reading next10 would have been fed a false 93% and a stale
next-10 queue that still listed already-closed outlet/scribe work.

## Fix (reproduced live)
Ran the deterministic generator: `python memory/goals/forecast_engine.py --json` => **RC=0**.
It recomputed from the live goal files in place (CWD-independent, __file__-anchored).

| artifact | BEFORE (stale) | AFTER (regenerated) |
|---|---|---|
| next10.json fleet | 84/90 (93.3%) gen 11-25 23:49 | **89/90 (98.9%)** gen 11-26 07:09 |
| forecast-latest.md | "Fleet: 84/90 (93%)" | **"Fleet: 89/90 (99%)"** gen 11-26 07:09 |
| next10 open queue | included closed outlet/scribe items | **orchestrator only** (Day-7 checkpoint, future-dated 12-02) |

## Agreement verification
- next10 fleet done/total == ledger fleet_reached/goals => **MATCH=True** (89/90 both).
- Ledger open-goal agents: {orchestrator: 1} only; next10 queue lists orchestrator only. The single
  remaining item is the Day-7 checkpoint (2026-12-02) — legitimately not yet due, correctly NOT closed.

## Verdict
PASS. Convergence forecast now agrees with SSOT ledger (99%). No false closure introduced; the one
open goal is genuinely future-dated. Recurring regeneration cadence (schtask) still absent from this
sandbox seat — same blocker as autonomy-score.json (see memory/ops/blockers.md); manual in-place
refresh done now, recurring automation to deploy on White.

## Honest gaps
- Did not register a recurring schtask (egress/admin wall from sandbox) — one-time refresh only.
- calibration.json history rotated by the run; not independently re-scored this pass (out of scope).
