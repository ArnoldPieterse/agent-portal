# Goal #4 Progress — 2026-11-17

**Status:** 2/7 valid days collected. Next step: accumulate 5 more daily runs.

## What was done this pass
1. Ran load_probe.py → hit WinError 10013 (sandbox egress block). All 260 requests failed.
2. Identified the bad entry in load-baseline.jsonl and removed it (would have polluted trend data).
3. Added **outage guard** to load_probe.py: if ALL requests at ALL levels fail, the script prints SKIPPED and writes nothing. Prevents future sandbox artifacts from corrupting the baseline.
4. Verified guard works: re-ran probe → "SKIPPED (all 260/260 requests failed)" — no write.

## Current baseline state
| Day | Timestamp | C10 p50 | C50 p50 | C200 p50 | Errors |
|-----|-----------|---------|---------|----------|--------|
| 1   | 2026-11-16 18:37 | 127.7ms | 373.4ms | 1666.2ms | 0 |
| 2   | 2026-11-17 14:27 | 108.2ms | 376.0ms | 1527.1ms | 0 |

Trend: C10 improving (-15%), C50 stable, C200 improving (-8%). No regression detected.

## Blocker for further data collection
Sandbox blocks localhost egress (WinError 10013). The probe MUST run from a context with network access to :8099. Options:
- Run manually from a non-sandboxed terminal daily
- Register schtask `PortalLoadProbe` once sandbox constraints lift (schtasks /create failed: Class not registered)

## Runbook note
**What broke:** load_probe.py wrote all-error entries when run in a network-restricted context, polluting the baseline.
**What fixed it:** outage guard added — all-fail runs are skipped with a log line instead of being appended to JSONL.