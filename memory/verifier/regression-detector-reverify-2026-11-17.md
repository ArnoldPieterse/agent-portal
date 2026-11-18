---
date: 2026-11-17T12:00:00Z
suite: regression-detector-reverify
pass: 2
fail: 0
total: 2
evidence_path: memory/verifier/regression-detector-reverify-2026-11-17.md
---
# Regression-detector re-verification (assists Mechanic #4)

Parent: memory/verifier/INDEX.md  |  Owner: **Mechanic** (goal #4, SLO pipeline "measures" leg)  |  Role here: Verifier = "enforces" leg
Date: 2026-11-17

## What was claimed (stale hot-note)
"synthetic +40% p95 spike correctly flagged REGRESSION_DETECTED; acceptance criterion met." Original demo (memory/mechanic/goal4-regression-demo-2026-11-17.json) injected a +60% spike and called analyze() directly — it did NOT check for false positives on real data, nor the all-error skip guard end-to-end.

## Independent reproduction (new)
Script: memory/verifier/regression-detector-reverify-2026-11-17.py -> output memory/verifier/regression-detector-reverify-2026-11-17.json. Three checks, all PASS:
1. **real_data_no_false_positive** — ran the detector over the ACTUAL on-disk baseline (memory/ops/load-baseline.jsonl, 2 days / 3 levels): 0 false positives. Detector does not cry-wolf on normal data.
2. **synthetic_spike_detected_at_c50** — +40% p95 spike injected at c=50 only; flagged=True at c=50 (ratio 1.4), clean at c=10/c=200. Detection is level-precise, not over-flagging.
3. **all_error_day_skipped** — mixed a portal-down day (errors==n all levels) into load_days(): guard excluded it (3->2 days), no phantom baseline / div-by-zero. Confirms the outage-skip guard survives on disk (corroborates Scribe/Verifier hot-note #1 closure).

## Verdict
Regression-detection sub-criterion of Mechanic #4 is **independently re-verified PASS** with a stricter test than the original demo.

## What remains OPEN on Mechanic #4 (NOT closed by this)
"one week of baseline data" = days 3-7 still missing. Blocker: daily schtask not running to accumulate real days (known, in memory/ops/blockers.md). Regression-demo half is done + now re-verified; do NOT mark #4 reached until days 3-7 land.
