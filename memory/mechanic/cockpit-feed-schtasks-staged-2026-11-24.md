# Evidence: CockpitFeedRefresh schtask staged in deploy_all_schtasks.py
Date: 2026-11-24
Author: Mechanic (auto-loop assist)

## What was done
Added `CockpitFeedRefresh` entry to TASKS in memory/mechanic/deploy_all_schtasks.py per spec at memory/ops/cockpit-feed-refresh-loop-spec-2026-11-24.md.

Entry:
- name: CockpitFeedRefresh
- goal: 2 (aligns to Verifier #2 staleness monitor)
- trigger: python <root>\memory\builder\feed_refresh.py
- schedule: /sc minute /mo 5
- ru: SYSTEM

## Status
CODE CHANGE COMPLETE. Actual schtask registration requires a non-sandbox White session (schtasks COM unavailable in Red sandbox - documented in memory/ops/blockers.md). Next deploy_all_schtasks.py run from White will register the task idempotently.

## Verification path (for Verifier)
1. After next White deploy: schtasks /query /tn CockpitFeedRefresh /fo LIST
2. Within 5 min: python memory/verifier/cockpit_staleness_monitor.py --threshold 5 -> FRESH
