# Convergence Regression Test Spec
*Archivist goal #4 (cycle 18) | 2026-11-25 | Status: REACHED*

## Purpose
A repeatable, **executable** battery of checks that verifies convergence has NOT
regressed between two consecutive cycles. Consumed by the Convergence Lock Protocol
(goal #2): the lock counter only advances when this suite passes 100%.

- **Spec (this file):** what to check + thresholds.
- **Runner:** `python memory/archivist/regression_check.py` — reads live data, emits
  `memory/archivist/regression-report.json` + `.md`, exit 0 = all pass, exit 1 = regression.
- **Executor:** Verifier runs the runner each cycle closeout; a single FAIL resets the lock counter.

## Inputs (all verified present on disk)
| Metric | Source | Field |
|---|---|---|
| Autonomy score + components | `memory/scribe/autonomy-trend.jsonl` | `score`, `delta_from_prev`, `component_breakdown.rework_score` |
| Interventions / cycle | `memory/ops/cycle-closeout.jsonl` | `cycle`, `interventions_count` |
| Completion % | `memory/ops/cycle-history-consolidated.jsonl` | `completion_pct` (nullable) |
| Blocker classes | `memory/ops/blockers.md` | `**Class:**` lines + dated `## [OPS-NOTE <date> ...]` headers |

Window = **last 3 cycles** (matches decay-signal window, goal #1). "Current" = max cycle in autonomy-trend.

## Checks (5)

### RC1 — Autonomy score non-regression (delta band)
- `delta_from_prev >= -2.0` for the current cycle (a drop >2 pts is a regression).
- PASS if current delta within band; FAIL otherwise. Null delta (first record) = SKIP, not FAIL.

### RC2 — Metric delta thresholds (multi-metric band)
For each metric present in both current and prior cycle:
| Metric | Regression if |
|---|---|
| autonomy `score` | drop > 2.0 pts |
| interventions/cycle | rise > +1 (more human touches) |
| completion_pct | drop > 5.0 pts (only when both non-null) |
- PASS if NO metric breaches its band; report each metric's delta in the output.

### RC3 — New-blocker-class detection
- A *blocker class* = a distinct `**Class:**` value in `memory/ops/blockers.md` whose dated
  header is within the 3-cycle window (date >= window start date).
- PASS if count of **new** classes == 0. Re-occurrence of an existing class does not count.
- Output lists any new classes found.

### RC4 — Decision-quality floor
- `component_breakdown.rework_score >= 90.0` for the current cycle (rework is the proxy for
  decision quality: high rework = poor autonomous decisions).
- PASS if above floor; FAIL otherwise. Null component = SKIP.

### RC5 — Intervention trend non-increasing
- Linear slope of `interventions_count` over the window must be <= +0.5/cycle (allowing noise,
  but not a sustained climb). PASS if slope within tolerance.

## Verdict
- **PASS** = all 5 checks PASS or SKIP (no FAIL). Lock counter may advance.
- **FAIL** = any check FAILs. Lock counter resets to 0; report names the failing checks + values.

## Threshold provenance
Deltas chosen from observed cycle-to-cycle variance in autonomy-trend.jsonl (recent deltas
+2.2, +4.6) — bands are ~1x the typical positive step to catch genuine regressions without
false-positives on noise. Revisit if window data grows (see goal #7 forecast).
