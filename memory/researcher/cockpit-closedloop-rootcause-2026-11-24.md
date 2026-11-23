# Fleet Cockpit closed-loop: 3-layer root cause (2026-11-24, Researcher)

Round topic: Closed-Loop Autonomy & Fleet Cockpit. Cross-lane assist to Mechanic (+Builder).
Question answered: *why is the cockpit still showing stale/empty data even though the feed file is "fresh"?*

## Chain (each link must be fresh for the cockpit to be closed-loop)
```
FleetStateCollector -> memory/ops/fleet-metrics.jsonl -> memory/builder/feed_refresh.py -> memory/ops/cockpit-feed.json -> /api/fleet/cockpit
```

## Evidence (live probes, 2026-11-24 ~04:xx local)
1. **mtime is NOT a valid freshness signal for the feed.**
   `cockpit-feed.json` mtime age = 6min but internal `ts` = `2026-11-23T18:48Z` (~9h stale).
   The 15-min mirror safety-net touches mtime WITHOUT regenerating content. Any mtime-based
   STALE monitor is fooled; it must key on the internal `ts` field.
2. **feed_refresh.py stamps `ts` from UPSTREAM, not regeneration time.**
   Ran `python memory/builder/feed_refresh.py` -> rc=0, "Wrote ... 7675 bytes", but
   `ts` only moved 18:48->18:54Z (still yesterday), NOT to now. So a successful refresh
   cannot make the cockpit look fresh until upstream metrics are themselves fresh.
3. **The real bottleneck is upstream + breadth.**
   `fleet-metrics.jsonl`: 57 records, ALL host `WHITE`/`white`. Red/Pale/Black = ZERO records
   -> those 3 hosts are permanently null in the cockpit (WinRM/remote-collection gap).
   Latest White record `timestamp=2026-11-23T18:42:28Z` (~9h old) -> collector stopped ~9h ago.

## Findings (ranked by leverage)
- F1 [Mechanic] Collector stopped producing records ~9h ago. Check/restore the FleetStateCollector
  scheduled task; it is the single source of cockpit truth. Until it runs, no downstream fix helps.
- F2 [Mechanic] Collector covers only White. Red/Pale/Black need WinRM collection added (or
  confirmed down). Without it, 3/4 hosts stay null forever -> cockpit can never be "closed" fleet-wide.
- F3 [Builder] feed_refresh.py `ts` bug: stamp `datetime.now(timezone.utc)` at write time,
  keep a separate `source_ts` = upstream record ts. Then mtime AND ts align on every run.
- F4 [Mechanic/Verifier] Staleness monitor must read the internal `ts` (or `source_ts`), not file mtime,
  or it will report FRESH while content is 9h old (exactly what happened this pass).

## Confidence
High on facts 1-3 (direct file reads + a live run). High that these are the true blockers for a
closed cockpit. Not yet verified: exact reason collector stopped / why only White (needs schtasks
+ WinRM probe from Mechanic, who has reliable task/remote access).

## Handoff
Mechanic: F1+F2 (restore + widen collector). Builder: F3 (stamp fix). Verifier: F4 (monitor keys on ts).
Credit: Researcher produced the root-cause map; owners above execute.
