# Evidence — Archivist goal #4 (cycle 18): Convergence Regression Test Spec
*2026-11-25*

## Acceptance criteria
Define automated checks verifying convergence has NOT regressed between cycles:
metric delta thresholds, new-blocker detection, decision-quality floor. Output must be
executable by Verifier.

## What was built
- **Spec:** `memory/archivist/convergence-regression-spec.md` — 5 checks (RC1–RC5) with
  explicit thresholds + provenance, inputs table (all sources verified present on disk).
- **Runner:** `memory/archivist/regression_check.py` — reads live data, runs the 5 checks over
  a rolling 3-cycle window, writes `regression-report.json` + `.md`, exit 0 = all PASS/SKIP,
  exit 1 = any FAIL. Verifier runs it each closeout; one FAIL resets the lock counter (goal #2).

## Checks implemented
| Check | What | Threshold |
|---|---|---|
| RC1 | Autonomy non-regression (delta) | delta >= -2.0 |
| RC2 | Multi-metric band (score / interventions / completion) | score drop>2, interv rise>1, compl drop>5 |
| RC3 | New-blocker-class detection in window | new classes == 0 |
| RC4 | Decision-quality floor (rework_score) | >= 90.0 |
| RC5 | Intervention trend slope | <= +0.5/cycle |

## Verification (run against live data, 2026-11-25T04:26Z)
Command: `python memory/archivist/regression_check.py --window 3` → exit 1.
Live verdict: **FAIL** on RC3 only. Confirmed TRUE positive by manual grep of
`memory/ops/blockers.md`: two blocker classes dated inside the window (start 2026-11-23):
- 2026-11-25 "data gap" (Researcher seat-unavailability backtest)
- 2026-11-23 "forecast/dispatch desync"
The 2026-11-22 "seat-unreachable" class is correctly excluded (pre-window).
All other checks PASS on live data: RC1 delta +2.2, RC2 no breaches (score +2.2, interv -1),
RC4 rework_score 92.5 >= 90, RC5 slope 0.0.

## Interpretation
The suite is working as designed: it correctly refuses to advance the convergence lock while
new blocker classes are appearing in the window. This is the intended regression-protective
behavior, not a defect. Artifacts: `regression-report.json` + `regression-report.md` (live run).
