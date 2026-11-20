# Evidence: perf_gate.py fail-closed on invalid baselines (2026-11-20)

**Goal:** verifier #1 (Performance Gate Baseline) — hardening step, NOT final closure.

## Problem found
`perf-baseline.json` had re-appeared as an ALL-NULL baseline (0/20 endpoints with p50, `captured_at 2026-11-20 13:09:44Z`, all `errors:12`). It was captured from a sandbox seat where :8099 is unreachable. The old `compare()` treated every endpoint as "N/A" and still exited **0 (PASS)** — a false pass that would have reported the fleet as healthy when nothing was actually measured.

## Fix (memory/verifier/perf_gate.py)
- New `baseline_validity(doc)` -> `(valid, n_valid, n_total)`; valid only if strict majority of endpoints carry a non-null p50.
- `capture_baseline()` now tags each baseline `"valid": true/false` and warns when invalid.
- `compare()` validates the baseline FIRST: if invalid it writes an INVALID-BASELINE report and **exits 3 (fail-closed)** without scoring or touching :8099.
- Docstring documents exit code 3.

## Proof (ran this pass)
1. `python memory/verifier/perf_gate.py --simulate` -> all phases PASS:
   - Phase 2: slowdown on /api/goals (5->1000ms) triggers alert (regression detection intact)
   - Phase 3: clean state = 0 regressions
   - Phase 4: all-null baseline flagged invalid (0/20); gate would exit 3
   - Phase 5: majority-valid baseline accepted (11/20)
2. `compare()` invoked directly against the REAL (invalid) baseline file -> `baseline_validity = (False, 0, 20)`, SystemExit code **3**, report written to memory/verifier/perf-report.md.

## Still open (goal #1 not closed)
Real live baseline still requires a non-sandbox White seat with :8099 egress to run `--baseline` and then 3 daily gate runs. That leg is blocked by the known :8099 egress wall (memory/ops/blockers.md, Verifier #4) — recorded once, not re-probed.
