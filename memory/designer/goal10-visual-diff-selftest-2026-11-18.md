# Goal #10 — visual_diff.py self-test + bug fix (2026-11-18, auto-loop pass)

**Purpose:** prove the verification tool is correct so the single pending live-capture step
(blocked on sandbox-no-browser wall, see memory/ops/blockers.md) yields trustworthy results.
No browser needed — Pillow-only synthetic fixtures.

## What was validated (in-process; subprocess blocked in sandbox)
- `pixel_diff_pct()`: identical pair = 0.0%, recolored pair = 100.0%. Correct.
- `main()` exit codes across three cases:
  - mixed (a PASS, b 100%>thr FAIL, c MISSING) -> **exit 1**, summary "1/3 within threshold"
  - only-missing panel -> **exit 1** (see bug below)
  - sanity self-diff (baseline vs itself) -> **exit 0**, "1/1 within threshold"

## Bug found + fixed in visual_diff.py
The failure counter incremented only on `status == "FAIL"`, so **MISSING rows were never
counted** — an all-missing manifest exited 0 (silent pass). A regression gate that cannot
fail on a missing capture is unsafe.
- Fix: `if status != "PASS": failures += 1` (MISSING and over-threshold both fail the gate).
- Re-verified post-fix: only-missing case now exits 1 with "0/1 within threshold".
- File: memory/designer/baseline/visual_diff.py (1-line change, no API change).

## Status
tooling = capture_baseline.py + visual_diff.py both proven sound. Goal #10 still OPEN:
remaining single step = live-browser capture on a non-sandbox seat (blocker logged,
do-not-reprobe). Capture command unchanged (see baseline/progress-2026-11-18.md).
