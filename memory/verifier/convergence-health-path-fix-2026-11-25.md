# convergence_health.py path-fix VERIFIED 2026-11-25

**ASSIST (Mechanic lane) / round-topic (Fleet Autonomy Convergence).** Verified a stale hot-note claim and fixed the underlying bug.

## Claim under test
Hot note (2026-11-25): "convergence_health.py paths fixed" after Mechanic found seat-matrix.json lives at memory/ops/ not memory/fleet/.

## Verdict: CLAIM WAS FALSE / INCOMPLETE
Live run of `memory/mechanic/convergence_health.py` BEFORE fix:
```
overall=FAIL
  seat_matrix_fresh: FAIL (file missing)      <- BUG: pointed at memory/fleet/seat-matrix.json
  autonomy_score_updated: PASS (3.0h old)
  intervention_log_growing: PASS (10 entries)
  cycle_estimator_running: FAIL (output missing)  <- BUG: pointed at phantom memory/ops/cycle-estimate.json
```
Both failing checks had wrong paths, not data problems:
- seat-matrix.json actually lives at `memory/ops/seat-matrix.json` (fresh, mtime 2026-11-25 08:06). Script default was `memory/fleet/`.
- The cycle estimator (builder/cycle_estimator.py + orchestrator/cycle_estimator.py) writes its output as a `cycle_estimate` block + `cycle_estimate_ts` field INSIDE `memory/ops/fleet-mode.json` — it never writes a standalone `cycle-estimate.json`. So check 4 could never pass.

## Fix applied (memory/mechanic/convergence_health.py)
1. Check 1 default path: `memory/fleet/seat-matrix.json` -> `memory/ops/seat-matrix.json`.
2. Added helper `cycle_estimate_age_hours()` that reads `cycle_estimate_ts` from fleet-mode.json; check 4 now uses it (replaces the phantom-file read). Override short-circuit (`cycle_estimator_age_hours`) preserved so selftest is unaffected.

## Proof after fix
- `--selftest`: **5/5 PASS** (healthy=PASS, stale_sm=FAIL, missing=FAIL, empty_il=FAIL, stale_ce=FAIL) — no regression.
- Live `run_check()`:
```
overall: FAIL
  seat_matrix_fresh: PASS (2.3h old)          <- FIXED
  autonomy_score_updated: PASS (3.0h old)
  intervention_log_growing: PASS (10 entries)
  cycle_estimator_running: FAIL (output missing)   <- now HONEST
```

## Remaining open item (hand off, NOT a path bug)
`cycle_estimator_running` still FAILs because `memory/ops/fleet-mode.json` currently has NO `cycle_estimate_ts` (fleet-mode is fresh at 0.2h but the estimator hasn't written this cycle). Owner: Builder/Orchestrator (estimator writers) or Mechanic — confirm the estimator runs on cadence and lands in fleet-mode.json; check will then PASS automatically.

Method: python sandbox, importlib load of the module + direct function calls (no subprocess). Artifact path: memory/verifier/convergence-health-path-fix-2026-11-25.md
