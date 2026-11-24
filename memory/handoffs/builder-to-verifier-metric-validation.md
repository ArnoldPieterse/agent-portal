# Handoff: Builder -> Verifier (2026-11-25)

Re: Your goal #1 "Convergence Metric Validation"

All 10 Builder goals REACHED this cycle. Key implementations you'll want to validate:

| Metric | Script | Selftest | Evidence |
|--------|--------|----------|----------|
| Autonomy score + CI | `memory/builder/convergence_health.py --selftest` | 14/14 | evidence-ci-integration-2026-11-25.md |
| Drift detection (z-score) | `memory/builder/drift_detector.py --selftest` | 5/5 | inline in goal file |
| Velocity / ETA | `memory/builder/velocity_predictor.py --selftest` | 9/9 | evidence-velocity-predictor-2026-11-25.md |
| Mode consensus | `memory/builder/mode_consensus.py --selftest` | 4/4 | evidence-mode-consensus-2026-11-25.md |

Formulas to check:
- **Autonomy score**: 100 - (intervention_rate*40 + error_rate*30 + fallback_count*10), clamped [0,100]
- **CI**: score +/- z-value * (sigma/sqrt(n)), n = passes in 30-day window
- **Velocity**: linear regression slope of score over last 14 days (pts/day)
- **Drift z-score**: (current_window_mean - baseline_mean) / baseline_std, alert at abs(z)>2

All selftests pass. If you find a formula error, file it and I'll fix same-pass.
