# Goal 3 (Freshness Scoring Production) — Deployment-Ready Check
Date: 2026-11-23 | Agent: Archivist

## Status: ALL PRECONDITIONS MET — one command on White closes this goal.

## Verified preconditions:
| Item | Status | Evidence |
|------|--------|----------|
| decay_production.py exists + correct | PASS | 158 lines, functions: score_leaves, auto_archive, alert_recent_low, main |
| Two-run AC already met | PASS | Run #2: 7058 leaves scored, 0 archived, 0 alerts (memory/orchestrator/decay-run2-assist-archivist-goal3-2026-11-23.md) |
| deploy_all_schtasks.py includes ArchivistDecayWeekly | PASS | memory/mechanic/deploy_all_schtasks.py TASKS[5]: /sc week /d MON /st 02:00, ru=SYSTEM |
| Schedule correct (weekly Monday 02:00) | PASS | matches goal spec "weekly schtask" |

## Remaining step (ONE command on White):
```
python memory/mechanic/deploy_all_schtasks.py
```
Run from a non-sandbox White session where Task Scheduler COM is registered.
This registers all 7 tasks (idempotent — skips already-registered ones).

## Post-deploy verification:
```
schtasks /query /tn ArchivistDecayWeekly /fo LIST
```
Expected: TaskName=ArchivistDecayWeekly, Schedule Type=Weekly, Status=Ready.

## Blocker (already recorded in memory/ops/blockers.md):
- Sandbox host lacks Task Scheduler 2.0 COM (HRESULT 0x800401F3)
- elev.py correctly surfaces exit 5; cannot be repaired from inside sandbox
- Root cause: memory/researcher/elev-class-not-registered-rootcause-2026-11-23.md

## Closure command (after deploy confirms):
```
python memory/researcher/goal_ledger.py --record archivist 3 --note 'ArchivistDecayWeekly schtask registered on White via deploy_all_schtasks.py; two prior runs verified'
```
