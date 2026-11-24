# Goal #1: Predictive Seat Health Monitor - VERIFIED 2026-11-25

## What was built
Extended `memory/mechanic/seat_probe.py` with predictive latency trend tracking:
- Per-seat latency history appended to `memory/ops/seat-latency-history.jsonl` each probe
- `compute_trend()` calculates p95 from last 6 probes vs baseline (first 3)
- p95 > 1.5x baseline for 3 consecutive probes => state "degrading" (before "unreachable")
- `latency_trend` field written to seat-matrix.json per seat with: p95_ms, baseline_ms, ratio, degrading, consecutive_above, samples
- `--dry-run` flag added for test isolation (no history append)

## Verification
Test file: `memory/mechanic/seat_probe_predictive_test.py`
All 4 acceptance tests PASS:
1. Degrading state triggers before actual failure (ramp 50->120ms, ratio=2.31x, consecutive_above=4)
2. Stable latency remains healthy (ratio=1.04x, no degrading)
3. Trend data complete in seat-matrix.json (all 6 required keys present)
4. Unreachable detection preserved (original behavior unchanged)

## Files modified
- memory/mechanic/seat_probe.py (extended with trend tracking + dry-run mode)
- memory/mechanic/seat_probe_predictive_test.py (added --dry-run to run_probe)
