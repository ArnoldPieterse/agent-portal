# Convergence Trajectory Model — built + run (2026-11-25)

Artifact: `memory/researcher/convergence_model.py`  |  Output: `memory/researcher/convergence-trajectory-results.json`

Dispatch #1 ("Convergence Trajectory Model") — NOT a repeat of `convergence_rate.py`
(which predicts when ONE metric crosses 10%-of-baseline). This is a multi-criterion
STEADY-STATE trajectory model aligned with round topic (Fleet Autonomy Convergence):
jointly tracks intervention_rate, error_free_rate, completion_pct -> composite convergence
index; steady-state gate = intervention <10% AND error-free >90%; consensus cycles-to-steady-state
with bootstrap 95% CI.

## Results
- Self-test (`--test`): PASS — graceful(<3)=insufficient_data (no fake number); synthetic >=4 pts -> R^2>0.7 + named bootstrap 95% CI; monotonicity holds.
- Real run: 7 points, status=ok, R^2(composite)=0.1378.
  - cycles_to_steady_state = 2 (CI95 bootstrap = [2, 96])
  - components: {'intervention_below_10pct': 0, 'errorfree_above_90pct': 2}

## Evidence-vs-inference / confidence (Researcher's skeptical read)
- EVIDENCE: model runs, self-tests all ACs, degrades gracefully, emits named CI. HIGH confidence in mechanics.
- INFERENCE/CAVEAT: real-data composite R^2 is only 0.14 — archive-derived per-cycle metrics are too
  noisy (n_goals varies 52..522; a few tiny n=10 cycles distort) to establish a tight trend. The point
  estimate (~2 cycles) sits inside a very wide CI [2,96]; treat as DIRECTIONAL, not precise.
- Recommendation: feed cleaner per-cycle inputs (mechanic's cycle-durations.jsonl + verified goal counts)
  rather than raw archive regex once available; re-run to tighten R^2 before using the ETA operationally.

Status: BUILT + SELF-TEST PASS + REAL RUN OK. Not a [verified:] closure of a numbered goal — my lane file is
already 10/10 verified (cycle 17); this is a new round-topic artifact recorded as an evidence leaf.
