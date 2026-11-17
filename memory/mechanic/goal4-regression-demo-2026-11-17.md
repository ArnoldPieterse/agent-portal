# Goal #4 - Regression Demo Caught

Date: 2026-11-17

## Test

Injected synthetic regression day (p95 ~60% above prior median) into load_trend.py analyze().

## Result: PASS

- c=10: p95 290.0ms vs median 187.6ms (+55%); p99 292.0ms vs median 188.2ms (+55%)
- c=50: p95 1200.0ms vs median 746.8ms (+61%); p99 1210.0ms vs median 748.4ms (+62%)
- c=200: p95 5400.0ms vs median 3325.6ms (+62%); p99 5420.0ms vs median 3331.6ms (+63%)

All 3/3 concurrency levels correctly flagged as regression.

## Status

Detector verified working. Real-data accumulation continues (2/7 days so far). Daily probe registered.
