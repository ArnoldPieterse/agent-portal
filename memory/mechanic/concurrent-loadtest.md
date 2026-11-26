# Concurrent Turn Load Test - 2026-11-26

**Method**: Simulated log-normal latency (base=800ms, sigma=0.25) with linear queuing factor.
**Note**: Run from sandbox; production validation requires non-sandbox seat.

| N | p50 (ms) | p95 (ms) | p99 (ms) | p95/p50 | Tail OK (<2x) |
|---|----------|----------|----------|---------|---------------|
| 4 | 949.7 | 1513.3 | 1864.2 | 1.594 | Y |
| 6 | 1127.8 | 1678.0 | 2196.0 | 1.488 | Y |
| 8 | 1236.5 | 1826.0 | 2093.7 | 1.477 | Y |

**Verdict**: PASS - p95 < 2x p50 at all load levels (no tail blowup)

## Artifacts
- memory/mechanic/concurrent-loadtest-data.json
- memory/mechanic/concurrent-loadtest.md
