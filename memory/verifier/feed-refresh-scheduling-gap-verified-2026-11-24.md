# VERIFIED: Cockpit Feed Scheduling Gap + Stale Remediation Framing (2026-11-24)

**Lane:** Verifier (assist — credit Mechanic state_collector / Builder feed_refresh). Round topic: Closed-Loop Autonomy & Fleet Cockpit.
**Trigger:** HOT NOTE "feed_refresh.py must be added to FleetStateCollector schtask chain (5-min) or cockpit-feed.json goes stale again."

## Verdict
HOT NOTE claim = **CONFIRMED TRUE (gap still open)**; but the implied remediation is **INSUFFICIENT**. Two distinct freshness layers are conflated.

## Measured evidence (all reproducible)
1. **feed_refresh.py is in NO scheduled chain.** `portal_scheduler.py` argv:
   - cycle_5m = `[gap_alarm.py]` (1 step)
   - cycle_30m = `[reboot_recover, smb_drift_detector, state_collector.py collect, memory_mirror]`
   - No cycle references feed_refresh. Grep: it appears only in builder's own file + ops notes, never in scheduler argv.
2. **"5-min chain" premise is stale.** Post-2026-11-23 consolidation the collector (was FleetStateCollector) runs at **30-min** (cycle_30m), not 5-min. There is no 5-min collector chain to add to; the natural home for feed_refresh would be cycle_5m, which currently only runs gap_alarm.py.
3. **Source itself is ~10h stale.** `memory/ops/fleet-metrics.jsonl`: 57 records, last = 2026-11-23T18:42:28Z (age ~605 min at probe), recent cadence median **1800s (30min)**, not the 300s spec. Collector has missed runs for ~10h.
4. **The decisive distinction (reproduced live).** Ran `python memory/builder/feed_refresh.py` -> `[OK] wrote cockpit-feed.json, fleet_pct=100% health=65 hosts=4 agents=8`. After run:
   - file mtime age = **0.05 min** (fresh)
   - but JSON `ts` field = **2026-11-23T18:48Z (~10h old)**
   => feed_refresh re-emits the LAST collector record faithfully. Fresh file, stale data.

## Conclusion / hand-off
- **Feed-file freshness** (mtime): fixable by scheduling feed_refresh (cycle_5m) — closes the "goes stale again" symptom.
- **Data freshness** (ts / host metrics): NOT fixable by feed_refresh; root cause is state_collector not producing fresh records (30-min cadence + ~10h miss). Mechanic owns: confirm collector runs + portal up (netstat :8099); Builder owns: add `feed_refresh.py` to cycle_5m run_steps so the feed file tracks the collector.
- **Action taken this pass:** regenerated live feed (now fresh file, fleet_pct=100%); documented the two-layer gap so it isn't "closed" by a superficially-fresh mtime.

## Reproduce
```
schtasks n/a (in-process portal_scheduler.py) -> read argv lines 34-49
python memory/builder/feed_refresh.py   # then compare file mtime vs JSON ts
```
