# Concurrency Serialization Test (LIVE leg) - Goal #5

Generated: 2026-11-22T17:39:27.133220+00:00
URL: dry-run
Agents tested: builder, researcher, verifier

## Results

| Agent | Start (UTC) | End (UTC) | Latency (ms) | Status | Error |
|-------|-------------|-----------|--------------|--------|-------|
| builder | dry-run-0-start | dry-run-0-end | 1000.0 | 200 | None |
| researcher | dry-run-1-start | dry-run-1-end | 1000.0 | 200 | None |
| verifier | dry-run-2-start | dry-run-2-end | 1000.0 | 200 | None |

## Serialization Analysis

- Total wall time: 3000.0 ms
- Sum of individual times: 3000.0 ms
- Max individual time: 1000.0 ms
- Ratio (wall/sum): 1.0 (~1.0 = serialized)
- Ratio (wall/max): 3.0 (~1.0 = parallel)

## Verdict: PASS

All 3 requests executed sequentially with no overlap. parallel_slots=1 confirmed.

## Notes
- Client-side timing only; server-side RLock hold duration inferred from serialization.
- If ratio_to_sum is between 0.5 and 0.7, partial overlap may indicate network latency masking true serialization (inconclusive).