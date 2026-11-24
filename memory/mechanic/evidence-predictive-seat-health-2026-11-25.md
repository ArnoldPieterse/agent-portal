# Predictive Seat Health Monitor - Evidence (Cycle 17, Goal #1)
Date: 2026-11-24 14:22 UTC

## What was built
Extended `memory/mechanic/seat_probe.py` with predictive latency trend tracking:
- Rolling window of last 10 probes per seat (stored in `memory/ops/seat-latency-history.jsonl`)
- p95 computation over current window vs baseline (median of prior readings)
- "degrading" state when ratio > 1.5x for 3+ consecutive probes
- Trend data written to `seat-matrix.json` under each seat's `latency_trend` field

## Verification (all PASS)
| Test | Result | Detail |
|------|--------|--------|
| Latency ramp triggers degrading before failure | PASS | p95=114.73ms, baseline=50ms, ratio=2.295, consecutive_above=4 |
| Stable latency stays healthy | PASS | ratio=1.038 (well below 1.5 threshold) |
| Trend data in seat-matrix.json | PASS | All 6 required keys present: p95_ms, baseline_ms, ratio, degrading, consecutive_above, samples |
| Unreachable detection preserved | PASS | Original cascade logic intact |

## Files modified/created
- `memory/mechanic/seat_probe.py` - extended with trend tracking (13,150 bytes)
- `memory/mechanic/seat_probe_predictive_test.py` - verification test suite
- `memory/ops/seat-latency-history.jsonl` - runtime latency data (auto-created)

## Key design decisions
- Baseline = median of readings BEFORE the current window (avoids self-referential comparison)
- Minimum 3 readings required before trend computation starts
- History capped at 50 entries per seat to prevent unbounded growth
- "degrading" state sits between "stale" and "unreachable" in priority: it fires while the seat is still responsive but getting slower
