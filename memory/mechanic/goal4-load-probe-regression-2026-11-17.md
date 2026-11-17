# Goal 4 — Load Probe: Regression Detection Added (2026-11-17)

**Step taken:** Upgraded `memory/ops/load_probe.py` with inline regression detection.
After each run, p95 at each concurrency level is compared to the previous entry;
if any level's p95 increased >20%, a `REGRESSION` alert line is appended to
`load-baseline.jsonl` with per-level deltas.

**Current baseline data:** 2 valid entries (Nov 16 18:37, Nov 17 14:27).
Sandbox egress block (errno 10013) prevented a third live run today;
a bad all-errors entry was written and immediately removed.

**Remaining for closure:**
- ~5 more daily runs on White (non-sandbox, where :8099 is reachable)
- One real or simulated regression to demonstrate the alert fires
  (e.g., temporarily slow an endpoint or inject artificial delay)

**Script status:** compiles clean (`py_compile` pass 2026-11-17).
Threshold: 20% p95 increase over prior run at any concurrency level.
