# Performance Gate Report

Run: 2026-11-20 13:54:52Z
Baseline: 2026-11-20 13:09:44Z

## INVALID BASELINE - gate refused to score (fail-closed)

Only 0/20 baseline endpoints have a real p50. An all/none-null baseline means the portal was unreachable when it was captured, so any PASS against it would be false.

Fix: re-capture from a non-sandbox White seat with :8099 egress:
  python memory/verifier/perf_gate.py --baseline
