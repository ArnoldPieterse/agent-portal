# Predictive Seat Health Monitor - Verification Evidence
Date: 2026-11-24T19:46:46Z

## What was built
Extended `memory/mechanic/seat_probe.py` with predictive latency trend tracking:
- New: `record_latency(seat, ms, ts)` - appends to seat-latency-history.jsonl (capped 200/seat)
- New: `load_latency_history(seat)` - reads per-seat samples
- New: `compute_trend(seat)` - p95 of last 3 probes vs median of prior history; >50% = degrading
- Modified: `build_matrix()` - includes per-seat trend dict + degrading_count in seat-matrix.json
- Modified: `main()` - prints degrading count, uses ~ marker for degrading seats

## Verification (test_seat_health_predictive.py)
3/3 tests PASS:
1. **degrading_triggers_before_failure**: latency ramp 50→80→120→200ms triggers degrading=True 
   (p95=120 vs baseline=50, +140%) while seat is still "active" (not >30min stale)
2. **stable_no_degrading**: constant 50ms does NOT trigger degrading
3. **matrix_includes_trend**: build_matrix() output includes trend field per seat + degrading_count

## Live probe run
`python memory/mechanic/seat_probe.py` → exit 2 (cascade: scribe unreachable, expected)
Output shows degrading=0, all seats have trend data in matrix.

## Files modified
- memory/mechanic/seat_probe.py (extended with predictive logic)
- memory/mechanic/test_seat_health_predictive.py (new test)
- memory/ops/seat-latency-history.jsonl (data file, auto-created on first probe)
