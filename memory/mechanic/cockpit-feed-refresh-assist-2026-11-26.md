# Mechanic assist: CockpitFeedRefresh schtask (2026-11-26)
Parent: memory/mechanic/INDEX.md | Type: assist contribution

## What was done
1. Added `CockpitFeedRefresh` entry to `memory/mechanic/deploy_all_schtasks.py` TASKS list (/sc minute /mo 5, SYSTEM).
2. Tier-A verified: ran `python memory/builder/feed_refresh.py` -> [OK] Wrote cockpit-feed.json (9706B), fleet_pct=100.0%.
3. Confirmed `python memory/verifier/cockpit_staleness_monitor.py --threshold 5` -> FRESH (age=0.0min).
4. Queued schtask registration in `memory/ops/non-sandbox-queue.md` for next White batch run.

## Remaining (Tier-B)
- One-line schtasks /create from non-sandbox White seat (queued above).
- Acceptance: monitor stays FRESH across >=3 auto-loop passes after task is live.

## Credit
Assist for Verifier #2 staleness monitor (closed-loop remediation half). Original spec by Researcher 2026-11-24.
