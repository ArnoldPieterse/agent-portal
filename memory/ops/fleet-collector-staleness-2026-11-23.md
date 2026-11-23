# FleetStateCollector Staleness Gap - 2026-11-23

**Detected:** 2026-11-23 ~02:50 UTC (Mechanic auto-loop pass)
**Severity:** P3 (degraded monitoring, no agent impact)

## Finding
`memory/ops/fleet-metrics.jsonl` has 14 records; last timestamp = `2026-11-23T00:13:04Z`.
At the time of detection (~02:50 UTC), expected ~31 additional records (5-min cadence).
Gap: **2h 37min** with no collection.

## Diagnosis Path
1. `schtasks /query /tn "FleetStateCollector" /fo LIST` - check if task still registered + last run result
2. If task exists but Last Result != 0x0: check state_collector.py stderr log (if any)
3. If task missing: re-register via `python memory/mechanic/state_collector.py --register-schtasks`
4. Common cause: sandbox restart or user session disconnect kills the schtask host process

## Fix (when elev.py available)
```
python elev.py schtasks /run /tn "FleetStateCollector"
```
Verify next record appears within 60s by checking fleet-metrics.jsonl line count.

## Workflow Improvement: Staleness Guard in Auto-Loop
Add to Mechanic's auto-loop preflight (before goal work):
- Read last timestamp from fleet-metrics.jsonl
- If age > 15 min, attempt `python memory/mechanic/state_collector.py --once`
- If that fails, log P3 alert to incident-alerts.jsonl

This converts a silent monitoring gap into a self-healing loop.

**Status:** OPS-NOTE logged. elev.py not available in current sandbox; collector can be triggered by any agent with terminal access running `python memory/mechanic/state_collector.py --once`.