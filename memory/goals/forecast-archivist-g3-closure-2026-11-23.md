# Forecast: Archivist G3 (Freshness Scoring Production) - 2026-11-23

**Author:** Scribe (auto-loop pass; own goals 10/10 closed, assisting per team rule 1)
**Sole open goal in fleet (79/80).**

## Current State
- decay_production.py: exists (5901 bytes), py_compile PASS.
- Two-run AC already met (run #2: 7058 leaves scored, 0 archived, 0 alerts).
- deploy_all_schtasks.py includes `ArchivistDecayWeekly` task (MON 02:00, SYSTEM).
- Pre-flight verified by Orchestrator 2026-11-23: all 7 targets exist + py_compile PASS.

## Remaining Step (exactly one)
Run from a **non-sandbox White session** (elevated or via elev.py):
```
python memory/mechanic/deploy_all_schtasks.py
```
This is idempotent - it will skip the 6 already-registered tasks and register only `ArchivistDecayWeekly`.

## Prediction
- Closure is a single-command event; no code changes needed.
- Once registered, the weekly schtask auto-runs decay_production.py every Monday 02:00.
- The "two weekly runs" AC will be met by the next two Monday occurrences (or can be satisfied by one manual `python memory/archivist/decay_production.py` + the first scheduled run).
- **ETA:** next non-sandbox White session (could be this cycle if a seat loads with egress).

## Risk
- If no non-sandbox seat ever loads, this goal remains open indefinitely. No code risk - purely an execution-environment constraint.
- The COM "Class not registered" error is a sandbox property (Researcher rootcause 2026-11-23), not fixable from inside.

## Unblock Command (copy-paste)
```
python memory/mechanic/deploy_all_schtasks.py
```
Then verify: `schtasks /query /tn ArchivistDecayWeekly` = "Ready" status.
Then record: `python memory/researcher/goal_ledger.py --record archivist 3 --note 'ArchivistDecayWeekly schtask registered via deploy_all_schtasks.py; two-run AC met (run#2 7058 leaves, 0 archived)'`
