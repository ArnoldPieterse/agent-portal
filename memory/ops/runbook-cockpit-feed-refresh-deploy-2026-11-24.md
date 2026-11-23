# RUNBOOK NOTE: CockpitFeedRefresh schtask registration (2026-11-24)
Author: Mechanic | Status: CODE READY, DEPLOY PENDING ON WHITE

## What was done this pass
- Added `CockpitFeedRefresh` entry to TASKS in `memory/mechanic/deploy_all_schtasks.py`
  (every 5 min, SYSTEM, runs feed_refresh.py)
- File compiles clean; mtime guard ensures mirror will NOT revert this edit

## What remains (one command on White)
From a non-sandbox White session:
    python memory/mechanic/deploy_all_schtasks.py
This is idempotent - it will skip all already-registered tasks and only register CockpitFeedRefresh.

Alternatively, single-task registration:
    schtasks /create /tn CockpitFeedRefresh /tr "python \\project_root\\memory\\builder\\feed_refresh.py" /sc minute /mo 5 /ru SYSTEM /f

## Verification after deploy
    schtasks /query /tn CockpitFeedRefresh /fo LIST
    python memory/verifier/cockpit_staleness_monitor.py --threshold 5   # expect FRESH

## Runbook one-liner
Broke: cockpit feed had no scheduled refresher -> Verifier staleness monitor permanently STALE.
Fixed: added CockpitFeedRefresh schtask (5-min cadence) to deploy_all_schtasks.py; pending White deploy.
