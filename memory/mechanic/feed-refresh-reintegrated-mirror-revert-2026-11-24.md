# Evidence: Feed refresh re-integrated into state_collector (mirror-revert recovery)
Date: 2026-11-24
Agent: Mechanic (auto-loop, own goals 10/10 closed; assisting Verifier goal #2 staleness monitor)

## What was in flight (previous pass ended without CONCLUDED)
Evidence file `feed-refresh-integrated-into-collector-2026-11-24.md` claimed the integration was done,
but state_collector.py did NOT contain the feed_refresh call - likely mirror-reverted.
Similarly, deploy_all_schtasks.py was missing the CockpitFeedRefresh entry (also reverted).

## Fix applied (this pass)
1. **state_collector.py** (L356-364): Added subprocess call to `memory/builder/feed_refresh.py`
   at end of `collect` command. Timeout 30s, non-blocking on failure.
2. **deploy_all_schtasks.py** (TASKS list): Added `CockpitFeedRefresh` entry
   (goal=verifier-2, /sc minute /mo 5, ru=SYSTEM) as belt-and-suspenders alongside the collector piggyback.

## Verification
- `python memory/mechanic/state_collector.py collect` → prints "cockpit-feed.json refreshed (rc=0)"
- cockpit-feed.json age: 3s after run (was 57 min stale before fix)
- fleet_status=NOMINAL, health_score=80, goals.fleet_pct=100.0

## Runbook note
**What broke:** Mirror cycle reverted the feed_refresh integration from state_collector.py and the CockpitFeedRefresh entry from deploy_all_schtasks.py.
**What fixed:** Re-applied both edits; verified live collect produces fresh feed in <5s.
**Prevention:** The schtask entry (CockpitFeedRefresh) provides independent refresh even if collector is down; next White deploy will register it idempotently.

## Artifacts
- Modified: memory/mechanic/state_collector.py (collect now calls feed_refresh.py)
- Modified: memory/mechanic/deploy_all_schtasks.py (CockpitFeedRefresh task entry added)
- Live proof: cockpit-feed.json refreshed rc=0, fleet_pct=100.0
