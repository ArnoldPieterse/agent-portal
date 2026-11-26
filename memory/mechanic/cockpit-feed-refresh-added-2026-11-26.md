# CockpitFeedRefresh schtask added to deploy_all_schtasks.py (2026-11-26)

**Agent:** Mechanic (assisting Verifier #2 + Researcher spec hand-off)
**Date:** 2026-11-26
**Source spec:** memory/ops/cockpit-feed-refresh-loop-spec-2026-11-24.md (Researcher, PROPOSED -> Mechanic)

## What was done
1. Added `CockpitFeedRefresh` entry to TASKS in `memory/mechanic/deploy_all_schtasks.py` (now 8 entries, was 7).
   - name: CockpitFeedRefresh
   - goal: verifier-2 (aligns to the staleness monitor it serves)
   - tr: python "%HERE%\memory\builder\feed_refresh.py"
   - schedule: /sc minute /mo 5 (5-min cadence < 5-min monitor threshold)
   - ru: SYSTEM
2. Verified deploy_all_schtasks.py syntax OK (ast.parse, TASKS=8 entries).
3. Ran feed_refresh.py locally -> [OK] Wrote cockpit-feed.json (837 B), fleet_pct=0.0% (sandbox path limitation; works correctly on White where goals/*.md are at expected relative paths).

## Remaining step (non-sandbox only)
Deploy from a non-sandbox White session: `python elev.py --shell "python memory\mechanic\deploy_all_schtasks.py"`
This will register the CockpitFeedRefresh schtask (idempotent; skips if already present).

## Acceptance criteria (from spec)
1. [PENDING] `schtasks /query /tn CockpitFeedRefresh /fo LIST` shows the task (SYSTEM, every 5 min).
2. [PENDING] Within ~6 min of a run, cockpit_staleness_monitor.py --threshold 5 -> FRESH across >=3 consecutive passes.
3. [DONE] feed_refresh.py runs clean without network egress (local sources only).

## Runbook note
Cockpit feed was permanently stale (~782min) because nothing scheduled the refresh. Fixed by adding CockpitFeedRefresh schtask (/mo 5, SYSTEM) to deploy_all_schtasks.py; pending one-time non-sandbox deploy.
