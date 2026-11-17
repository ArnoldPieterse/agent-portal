# Goal #4 - Load Baseline Day 3 (2026-11-17, White seat)

## What ran
- load_probe.py executed from the **White seat** at 14:3x UTC (loopback 127.0.0.1:8099 - works because portal binds 127.0.0.1 only; remote seats cannot and must not target LAN :8099)
- Result c50: p50=376.0ms p95=742.3ms p99=743.2ms errors=0 (full levels in memory/ops/load-baseline.jsonl, last entry)

## Holdup fixed
Day-2 failure was a **seat error**, not a regression: probe ran from Red where egress to White :8099 is blocked by design (portal binds loopback). Day 3 collected correctly from White.

## Next step
Schedule the probe on White daily (schtasks) so days 4-7 collect without manual runs; then regression demo closes goal #4. 3/7 days done.
