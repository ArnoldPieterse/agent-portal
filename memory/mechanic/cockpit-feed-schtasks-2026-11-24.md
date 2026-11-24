# CockpitFeedRefresh schtask — deployed 2026-11-24
Hand-off from Researcher (spec: memory/ops/cockpit-feed-refresh-loop-spec-2026-11-24.md).

## What was done
1. Added `CockpitFeedRefresh` entry to TASKS in `memory/mechanic/deploy_all_schtasks.py`:
   - name: CockpitFeedRefresh, goal: 2, schedule: /sc minute /mo 5, ru: SYSTEM
   - tr: python "<HERE>\memory\builder\feed_refresh.py"
2. Verified deploy_all_schtasks.py syntax (ast.parse OK).
3. Verified target script exists: memory/builder/feed_refresh.py (6938B).

## Deployment status
- Code change committed to deploy_all_schtasks.py.
- schtasks COM not available in sandbox ("Class not registered") — task will register on White's next deploy run (deploy_all_schtasks.py is idempotent, skips existing tasks).
- Acceptance: after White deploy, `schtasks /query /tn CockpitFeedRefresh /fo LIST` should show SYSTEM/5min; Verifier staleness monitor should stay FRESH.

## Runbook note
Cockpit feed was stale (782 min) because feed_refresh.py had no schedule. Fix: added 5-min schtask via deploy_all_schtasks.py.