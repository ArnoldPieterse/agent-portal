# Predictive Seat Health Monitor - Evidence

Date: 2026-11-24T16:13Z
Goal: Extend seat_probe.py with p95 latency trend tracking; >50% rise over 3 probes = "degrading" state.

## What was done
1. Added `seat-latency-history.jsonl` (memory/ops/) - appends per-probe timestamp + portal_ok + latency_ms
2. Added `percentile()` helper - linear-interpolation p95 computation
3. Added `compute_trend()` - reads last 200 entries, splits into recent(3) vs baseline(6), computes ratio
4. Modified `determine_state()` to accept trend_state; returns "degrading" when seat is reachable but p95 ratio > 1.5
5. Matrix output now includes `trend` block (recent_p95_ms, baseline_p95_ms, ratio, state, threshold) and `degrading_count`
6. Exit code: degrading seats trigger exit 1 (same as degraded)

## Verification
- Synthetic test: 6 fast probes (10-20ms) + 3 slow probes (50-70ms) → ratio=3.538, state="degrading" PASS
- Stable test: uniform latencies → ratio=1.159, state="stable" PASS  
- Insufficient data: 3 entries only → state="insufficient_data" PASS
- Live run: probe executes cleanly, writes matrix + history, trend="insufficient_data" (expected - portal down)

## Files modified
- memory/mechanic/seat_probe.py (extended with trend tracking)
- memory/ops/seat-latency-history.jsonl (new, auto-created on first probe)
- memory/ops/seat-matrix.json (now includes trend block + degrading_count)
