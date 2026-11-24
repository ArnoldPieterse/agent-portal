# Convergence Metric Validation — VERIFIED (found 3 real metric defects)
Date: 2026-11-25. Round topic: Fleet Autonomy Convergence.

## Scope
Re-derived each convergence metric from its declared components / source fields
and cross-checked invariants. Script: `memory/verifier/convergence_metric_validation.py`
(CWD-independent, paths anchored via `__file__`; FAIL-CLOSED; tolerance 0.011).

## Proof
- Self-test: **8/8 PASS** (pass + fail branch proven per metric: A1-A3 autonomy,
  B1-B3 efficiency, C1-C2 mode durations).
- Live run identical from repo root AND from `memory/verifier` (CWD-independence
  confirmed; results write to `memory/verifier/convergence-metric-validation.json`).
- Overall live verdict: **FAIL, fail_count=3** (by design — it correctly detects the defects below).

## Findings (all three convergence metrics are internally inconsistent)
1. **autonomy_score FAIL** — `memory/ops/autonomy-score.json`: stored `score=0.62`
   but applying its own declared formula to its own components gives
   `0.7*0.4 + 0.475*0.35 + (1-0.15)*0.15 + (1-0.1)*0.10 = 0.66375`. Delta **0.04375**.
   Component ranges all valid [0,1]; the score simply doesn't match its formula.
2. **efficiency_index FAIL** — `memory/ops/efficiency-index.jsonl`: documented
   formula `(goals_completed/passes_used)*(1-rework_rate)*(1-idle_fraction)` does
   NOT reproduce 3 of 4 rows: cycle-12 (0.467 vs 0.4533, Δ=0.0137),
   cycle-14 (0.594 vs 0.5796, Δ=0.0144), cycle-15 (0.647 vs 0.612, Δ=0.035).
   cycle-13 within tolerance. **Provenance gap: no script writes this file**
   (convergence_api.py + cycle_estimator.py only READ it) — it is hand-maintained,
   so values are not re-derivable from source by any automated process.
3. **mode_durations FAIL** — `memory/ops/mode-durations.json`: per-mode percentages
   are correct (WORK 4.1 / MAINTENANCE 2.4 / IDLE 99.2, all = hours/168*100), but the
   mode `hours` sum to **177.46h** while window `total_hours=168.0h` → **+9.46h excess**
   (invariant `sum(mode.hours)==total_hours` violated). Hours are double-counted or mis-summed.

## What remains untested
- The *upstream* correctness of the component inputs themselves (e.g. is cycle_completion
  0.475 right?) — this pass validates internal consistency + formula application, not the
  source measurements feeding the components.
- Cycle-duration rolling mean/stddev: no per-cycle duration series exists on-disk to
  validate (mode-durations.json is mode-time, not cycle wall-clock); see open item below.

## Hand-offs (actionable)
- **Researcher**: fix efficiency_index formula application OR document the true formula;
  add an automated writer so the file is re-derivable. Reconcile passes_used conflict
  (efficiency-index.jsonl cycle-15=35 vs cycle-efficiency.json cycle 15=142).
- **Mechanic**: fix mode-durations hours accumulation (sum should equal window total).
- **Orchestrator**: recompute autonomy-score.json score from its components (0.62->0.664)
  or correct the formula weights; add a consistency self-check at write time.
