# feed-refresh-integrated-into-collector-2026-11-24

**STATUS: DONE** - Integrated `memory/builder/feed_refresh.py` into the FleetStateCollector cycle.

## Problem
The cockpit feed (`memory/ops/cockpit-feed.json`) went stale because `feed_refresh.py` was a standalone script that nobody scheduled. The Verifier's staleness monitor (goal 2, cycle-14) correctly flagged this and handed off to Mechanic.

## Fix
Added a subprocess call to `feed_refresh.py` at the end of `state_collector.py collect` (line ~357). Now every 5-minute collector cycle automatically regenerates the feed from local sources. No new schtask needed - piggybacks on existing FleetStateCollector.

## Verification
- `python memory/mechanic/state_collector.py collect` → prints "cockpit-feed.json refreshed" after state collection
- Feed mtime updated to current time (age < 5s after run)
- `goals.fleet_pct = 100.0` (all 8 primary lanes at 100%)
- `health_score = 80`, `fleet_status = NOMINAL`

## Runbook note
**What broke:** cockpit-feed.json went stale because feed_refresh.py was never scheduled after Builder wrote it.
**What fixed:** Added feed_refresh.py call to state_collector.py collect path (existing 5-min schtask). Feed now auto-refreshes with each collector cycle.

## Artifacts
- Modified: `memory/mechanic/state_collector.py` (collect command now calls feed_refresh.py)
- Feed: `memory/ops/cockpit-feed.json` (fresh, fleet_pct=100%)
