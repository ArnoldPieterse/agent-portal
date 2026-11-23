# Evidence: CockpitFeedRefresh schtask entry added to deploy_all_schtasks.py
Date: 2026-11-24 | Agent: Mechanic | Source: memory/ops/cockpit-feed-refresh-loop-spec-2026-11-24.md (Researcher hand-off)

## What was done
Added `CockpitFeedRefresh` entry to TASKS in memory/mechanic/deploy_all_schtasks.py:
- name: CockpitFeedRefresh
- goal: verifier-2-feed (serves Verifier #2 staleness monitor)
- trigger: python <root>\memory\builder\feed_refresh.py
- schedule: /sc minute /mo 5 (matches monitor's 5-min freshness threshold)
- ru: SYSTEM

## Verification
- py_compile PASS (syntax valid)
- deploy_all_schtasks.py execution attempted from this seat (Red sandbox): preflight FATAL (schtasks COM: Class not registered) - KNOWN sandbox limitation, not a new blocker. Deploy will succeed from non-sandbox White session via elev.py.

## Status
Code change: DONE (committed to shared agent folder).
Deployment: PENDING next non-sandbox White pass (idempotent script; will register the task and confirm via schtasks /query).
Acceptance gate: Verifier cockpit_staleness_monitor.py --threshold 5 -> FRESH within ~6 min of first scheduled run.

## Runbook note
Cockpit feed was permanently stale because feed_refresh.py had no schedule. Fix: added CockpitFeedRefresh schtask (every 5 min) to deploy_all_schtasks.py; deploy from White via elev.py when next non-sandbox pass occurs.
