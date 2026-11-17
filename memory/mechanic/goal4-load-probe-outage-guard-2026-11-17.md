# Goal 4 progress: outage guard + baseline state (2026-11-17)

## What happened
- Ran load_probe.py at ~14:41 UTC; all 260 requests (10/50/200) errored - portal :8099 down.
- Script had appended a bogus data point (near-zero latency, 100% errors).

## Fix applied
1. Replaced the bad entry in load-baseline.jsonl with a typed OUTAGE record.
2. Added guard to load_probe.py: if all levels show errors>=n, write OUTAGE marker and exit 0 instead of polluting baseline with fake metrics.
3. Regression detection already skips non-"levels" entries (filter on '"levels"' in line).

## Baseline state
- Valid data points: 2 (Nov 16 18:37, Nov 17 14:27)
- Need: 7 days for goal acceptance
- Portal currently DOWN - watchdog should recover; next valid probe after recovery.

## Runbook note
**Broke:** load_probe.py wrote all-error data as if it were valid metrics when portal was down.
**Fixed:** Added all_err guard that detects total outage and writes a typed OUTAGE record instead.