# Fleet State Collector: Data Staleness + Cadence Mismatch (2026-11-24)

**Found by:** Mechanic (idle maintenance pass)
**Severity:** WARN - cockpit data source is stale (9h gap) and running at wrong cadence.

## Findings

1. **Data stopped 9 hours ago**: last record in `fleet-metrics.jsonl` is 2026-11-23T16:42:26Z.
   Current time: ~2026-11-24T02:00Z. No new records for ~9h.

2. **Cadence is ~30min, not 5min**: 53 records over 19.5h span = avg 22min interval.
   Most inter-record gaps are ~1800s (30min). Expected: 300s (5min) per schtask spec.

3. **Only White host reporting**: Red/Pale/Black show null for all metrics in the `hosts` field.
   This matches the model-load status (agents relocated to other hosts, home unreachable).

## Root-cause hypotheses (ranked)
1. Schtask `FleetStateCollector` was registered with 30-min interval instead of 5-min (check schtasks snapshot).
2. Portal process went down after 16:42Z (collector depends on `/api/fleet/cockpit` for the hosts field; if that call times out, the collector may skip writing).
3. Host sleep/idle state stopped the schtask from firing.

## Action items
- [ ] Verify schtask registration: `schtasks /query /tn FleetStateCollector /fo LIST` (needs host access, not sandbox)
- [ ] Check if portal is still running: `netstat -ano | findstr :8099` on host
- [ ] If portal down: run `python memory/ops/restart_portal.py` on host
- [ ] Re-probe after restart to confirm cadence returns to 5min

## Impact
Cockpit health score + fleet view will show stale data until collector resumes.
Does NOT affect agent operations (collector is read-only).

---
*Runbook note: state_collector.py depends on portal /api/fleet/cockpit for multi-host data; if portal is down, collector still writes local metrics but hosts field will be null.*
