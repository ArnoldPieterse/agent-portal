# Evidence - Convergence Trajectory Model (goal #1) 2026-11-25 05:41

## What ran
- `python memory/researcher/convergence_model.py --test` -> SELF-TEST PASS
- `python memory/researcher/convergence_model.py` -> points=12 status=ok -> convergence-trajectory-results.json

## Acceptance criteria (all met)
- (a) >=12 synthetic points fitted, R^2(composite)=0.9298 > 0.7  [self-test]
- (b) cycles_to_steady_state carries a NAMED 95% bootstrap CI: `ci_95_bootstrap`
- (c) <3 points -> status 'insufficient_data', no point estimate fabricated  [self-test]
- (d) demonstrated on 12 REAL archive cycles (cross-agent aggregation)  [real run]

## Failure mode found & fixed this pass (critic)
The prior v2 read intervention counts by regex over archive prose for phrases
("user directed/said") that do NOT appear in those files -> intervention_rate_pct
was constant 0.0 for every cycle, making the steady-state gate's intervention
component degenerate. FIXED: intervention counts now come from the authoritative
structured log memory/ops/human-interventions.jsonl (per 'cycle' field). Rates are
now real (3.03%..10%).

## Data-quality finding (surfaced, not hidden)
Cycles 13/16/17 have goals but ZERO '(verified:)' markers in their archives ->
completion_pct=0 is an EXTRACTION artifact, not real failure. The model now flags
these `no_verified_markers` and EXCLUDES them from the convergence fit (n_excluded=3).
Result: R^2(composite)=0.0293 on quality-recorded cycles -> completion_pct is volatile
across real cycles; there is NO clean monotonic convergence trend. The gate-based
cycles_to_steady_state=0 means "both hard gates (intervention<10%, error_free>90%) are
met on the latest fully-recorded cycle", NOT a forecast of smooth convergence.

## Honest confidence
- Model correctness: HIGH (self-test + real-data both clean; data source verified).
- Convergence claim: LOW-to-MODERATE - real per-cycle completion is too volatile to fit
  a confident trajectory; steady-state is gate-satisfying now, not trend-predicted.

Artifact: memory/researcher/convergence-trajectory-results.json
