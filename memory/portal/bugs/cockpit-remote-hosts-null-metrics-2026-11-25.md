# BUG: cockpit + over-time views showed only White used (Red/Pale/Black read as idle)

**Reported:** 2026-11-25, user: "show host usage over time - it seems we have only used white
while pale, red and black have been sitting idle". **Status: FIXED same turn.**

## Symptom
Every host-usage-over-time view (Cockpit tab VRAM bars, topology, fleet-metrics.jsonl,
cockpit-feed.json) carried real numbers for White only; Red/Pale/Black were null -> rendered
as "—"/N/A -> looked idle. In reality Pale was busy (47% VRAM, 69-90°C) and Red had models
resident. Black WAS genuinely near-idle: zero models loaded on its Studio.

## Root cause (three stacked gaps)
1. `agent_portal.py _cockpit_snapshot()`: local seat via nvidia-smi, remote seats hardcoded
   `{vram_pct: None, cpu_pct: None, temp_c: None}` with comment "metrics null until probed" -
   but NOTHING ever probed them.
2. `memory/builder/feed_refresh.py` (writes cockpit-feed.json) was never scheduled in any
   portal_scheduler job -> feed sat 35h stale; coverage gate (cockpit_coverage_check.py,
   threshold 5min) could never pass.
3. `memory/builder/state_snapshot.py get_host_resources()`: only read stale probe files or a
   hardcoded null list containing phantom host "Blue" -> fleet-snapshots.jsonl 100% blind.

## Fix (2026-11-25)
1. `_cockpit_remote_probe(base)`: each remote seat's Studio exposes the same GPU facts on
   `/api/system` (devices[]: vram_used_gb, gpu_utilization_pct, temperature_c). Keys from
   agents.json seats, host_api.py fallback for catalog-only hosts (Black). Parallel probes,
   20s per-host cache over the 15s cockpit TTL, failure degrades to null (never breaks cockpit).
2. `feed_refresh.py` added to cycle_10m (portal_scheduler.py); coverage gate threshold
   5 -> 12 min (a 5-min gate can never pass against a 10-min writer; the gate's real job is
   completeness = non-null per host).
3. `state_snapshot.py` now sources hosts from /api/fleet/cockpit; fallback list fixed
   White/Black/Red/Pale.

## Verify
`GET /api/fleet/cockpit` -> all 4 hosts non-null; `python memory/ops/cockpit_coverage_check.py`
-> "OK: FRESH AND COMPLETE, hosts_complete=4". fleet-metrics cadence is cycle_30m (30 min),
so remote history only accumulates from 2026-11-25 16:58 UTC - no backfill possible.

## Open thread
Black has NO resident models while Builder/Verifier/Pixel/Forge are seated there - first work
for them pays a full model load. Candidate: boot-time load recipe for .99 (see hotload catalog).
