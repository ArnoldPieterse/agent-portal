# Evidence: Fleet Autonomy Convergence Trend Analyzer (2026-11-26)

Round topic: **Fleet Autonomy Convergence** — new artifact, not a re-verify.

## What was built
`memory/forge/convergence_trend.py` — reads the historical
`consistency-report.jsonl` (21 runs) + `drift-report.jsonl` (29 scans) and computes:
- per-host reachability % across all consistency runs
- verdict distribution (PASS/WARN/CRIT)
- config-hash distinct set + mismatch count
- drift status distribution + **unresolved-drift detection**
- a single 0-100 convergence score + projection

## Fresh measurement this pass
```
$ python memory/forge/convergence_trend.py
  consistency runs : 21   drift scans: 29
  verdicts         : {'PASS': 21}
  host reach %     : {'White': 0.0, 'Red': 100.0, 'Pale': 100.0, 'Black': 0.0}
  config mismatch  : 0 runs   model mismatch: 0 runs
  distinct hashes  : ['1cbfc6f19c28']
  drift statuses   : {'CLEAN': 26, 'DRIFT': 3}   events: 0
  CONVERGENCE SCORE: 90.0/100
  regression       : False   gated-on-recovery: True (down: White,Black)
  VERDICT          : TRENDED-CONVERGED
```
`--json` path emits pure valid JSON (verified json.loads OK).

## Data-quality bug caught + fixed (the real finding this pass)
First version of the analyzer flagged **REGRESSION** (score 87.4) because it counted
3 "DRIFT" entries in `drift-report.jsonl` as real regressions. Inspecting them:
- entry 1 (09:05:51): orphaned `test_dummy.py` — the initial detector selftest dirty-case
- entries 17,18 (14:09): introduced-dep demos (wf1/wf2/wf3)

Each is **immediately followed by a CLEAN scan** (baseline updated / test artifact
removed) — i.e. selftest/simulate artifacts written to the same jsonl as live scans,
NOT production regressions. The drift log had no field distinguishing them.

Fix: a drift entry now counts as an unresolved regression **only if no later scan is
CLEAN** (walk newest->oldest; a CLEAN resets). Selftest dirty-cases are resolved by the
subsequent baseline update and are auto-excluded (`drift_selftest_resolved=3`,
`drift_unresolved=0`). This is the measurement-honest rule: a real regression persists at
the tail of the log; a selftest does not.

## Why score is 90, not 100
Score = 40*verdict + 25*consistency + 25*drift_clean + 10*reach_floor.
- verdict PASS=21/21 -> 40
- config/model mismatches=0 -> 25
- unresolved drift=0 -> 25
- reach_floor = min host pct = White/Black at 0% (down per model-load status) -> 0

So the fleet is **fully converged on consistency + pipeline drift**; the only gap is
host reachability for White+Black, which is a model-load/environment constraint, not a
gate-logic failure. `gated-on-recovery=True` records that full-confidence (4/4 host)
verification resumes automatically when those hosts return.

## Verdict
TRENDED-CONVERGED. No open Forge goals remain (all 4 [REACHED]); this pass produced a
new reusable convergence-scoring tool + fixed a selftest-pollution data-quality bug in the
drift log interpretation. Report appended to `memory/forge/convergence-trend-report.jsonl`.

(verified: 2026-11-26 auto-loop pass - Forge: convergence_trend.py built and run live;
score 90.0, VERDICT TRENDED-CONVERGED, regression=False, drift_unresolved=0,
selftest_resolved=3; --json parses clean. Artifacts: memory/forge/convergence_trend.py,
memory/forge/evidence-convergence-trend-20261126.md, memory/forge/convergence-trend-report.jsonl)
