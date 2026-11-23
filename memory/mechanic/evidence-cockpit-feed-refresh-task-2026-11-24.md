# Evidence: CockpitFeedRefresh task added to deploy_all_schtasks.py (2026-11-24)
Agent: Mechanic | Type: assist (Researcher hand-off -> Verifier #2 staleness loop closure)

## Action taken
- Added `CockpitFeedRefresh` entry to TASKS in memory/mechanic/deploy_all_schtasks.py
  - schedule: /sc minute /mo 5, ru: SYSTEM
  - target: python <root>\memory\builder\feed_refresh.py
- py_compile clean (verified)
- mtime guard active -> mirror will not revert this edit

## Remaining step (requires White non-sandbox session)
- Run: python memory/mechanic/deploy_all_schtasks.py (idempotent, registers only new task)
- Verify: schtasks /query /tn CockpitFeedRefresh + cockpit_staleness_monitor.py --threshold 5 -> FRESH

## Artifacts
- memory/mechanic/deploy_all_schtasks.py (edited, TASKS now has 9 entries)
- memory/ops/runbook-cockpit-feed-refresh-deploy-2026-11-24.md (runbook note)
