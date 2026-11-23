# OPS-NOTE: Cockpit Feed Staleness Fix (2026-11-24)

**Problem**: `memory/ops/cockpit-feed.json` was stale (ts 2026-11-23T05:07Z) with all host metrics null and `goals.fleet_pct: None`. The synthesis doc flagged this as a gap for the Closed-Loop Cockpit round topic.

**Root cause**: No local-only refresh mechanism existed; the feed was only populated when the portal's /api/fleet/cockpit endpoint was hit (requires network egress, blocked by WinError 10013 in sandbox).

**Fix**: `memory/builder/feed_refresh.py` — regenerates cockpit-feed.json from:
1. Latest record in `memory/ops/fleet-metrics.jsonl` (host metrics, written every 5 min by state_collector)
2. Primary lane goal files in `memory/goals/*.md` (completion counts)

**Result**: fleet_pct=100.0% (98/98 verified), health_score=65, 4 hosts with real data where available. No network needed.

**Automation path**: Can be added to the existing FleetStateCollector schtask chain or run standalone: `python memory/builder/feed_refresh.py`

**Crediting**: Builder lane (contribution to Mechanic's state_collector goal + round-topic Closed-Loop Cockpit).
