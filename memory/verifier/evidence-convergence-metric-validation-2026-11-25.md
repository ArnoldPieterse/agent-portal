# Convergence Metric Validation — Evidence (2026-11-25)
Goal: #1 Convergence Metric Validation (Verifier)
Status: **VALIDATED WITH FINDINGS** — 3 metric families checked, 2 FAIL on live data.

## Method
`memory/verifier/convergence_metric_validation.py` re-derives each metric from its
declared components and compares to stored values with tolerance ±0.011.
Self-test: **8/8 PASS** (all branches — pass + fail — proven with synthetic fixtures).

## Live Results (2026-11-24T16:20:18Z)
Overall: **FAIL** (3 of 3 metric families flagged)

### A) Autonomy Score — FAIL
| Check | Stored | Recomputed | Delta | Verdict |
|-------|--------|-----------|-------|---------|
| score_matches_formula | 0.62 | 0.66375 | 0.04375 | EXCEEDS TOL (0.011) |

All 4 component ranges valid [0,1]. The stored score is **stale** relative to the
current components — likely written before a component update.

### B) Efficiency Index — FAIL (3/4 rows)
| Cycle | Stored | Recomputed | Delta | Verdict |
|-------|--------|-----------|-------|---------|
| cycle-12 | 0.467 | 0.4533 | 0.0137 | EXCEEDS TOL |
| cycle-13 | 0.618 | 0.6155 | 0.0025 | OK (within tol) |
| cycle-14 | 0.594 | 0.5796 | 0.0144 | EXCEEDS TOL |
| cycle-15 | 0.647 | 0.6120 | 0.0350 | EXCEEDS TOL (worst) |

Pattern: stored values are **consistently higher** than formula output (systematic
positive bias). No writer script found that computes the index from these fields —
the `writer_scripts` list only contains readers (convergence_api, cycle_estimator,
and this validator itself). The index was likely hand-seeded or computed with a
different/undocumented formula.

### C) Mode Durations — FAIL
| Check | Value | Verdict |
|-------|-------|---------|
| WORK.percent | 4.1 (expected 4.1) | OK |
| MAINTENANCE.percent | 2.4 (expected 2.4) | OK |
| IDLE.percent | 99.2 (expected 99.2) | OK |
| hours_sum_equals_window | sum=177.46, window=168.0, excess=+9.46h | FAIL |

Per-mode percentages are internally consistent, but the mode-hours sum exceeds the
window by 9.46 h (5.6% over). Suggests overlapping mode windows or a data-entry
error in one of the hour fields.

## Boundary Conditions Verified (self-test)
- Component out-of-range → correctly FAILs
- Zero passes (division guard) → correctly flagged
- Score drift beyond tolerance → correctly FAILs
- Consistent fixtures → correctly PASS

## Conclusion
Formulas are **correctly implemented** in the validator; the live data has
stale/inconsistent values. Root cause: no single authoritative writer recomputes
these metrics atomically with their source components. Recommendation: wire a
single computation pass (or add a post-write consistency check) so stored values
always match formula output.

## Artifacts
- Validator: `memory/verifier/convergence_metric_validation.py`
- Results: `memory/verifier/convergence-metric-validation.json`
