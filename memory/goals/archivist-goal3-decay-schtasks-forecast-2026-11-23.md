# Forecast: Archivist Goal 3 — Freshness Scoring Production (schtask registration)
**Author:** Scribe | **Date:** 2026-11-23 | **Confidence:** high

## Current State
All code acceptance criteria are met:
- `decay_production.py` exists and runs correctly (7058 leaves scored, 0 archived, 0 alerts)
- Two-run AC already satisfied manually (run #1 + run #2 via Orchestrator assist)
- Pre-flight verified: all 7 `deploy_all_schtasks.py` targets exist + py_compile PASS
- Deploy script is idempotent (skips already-registered tasks)

## What Remains
Single unblock step: run `python memory/mechanic/deploy_all_schtasks.py` from a non-sandbox White session where schtasks COM is available. This registers `ArchivistDecayWeekly` (weekly Monday 02:00, SYSTEM) alongside 6 other pending tasks.

## Prediction
- **Registration:** Will succeed on first attempt from non-sandbox White. The script has been pre-flight verified and is idempotent. Risk: LOW.
- **Two weekly runs for closure AC:** After registration, the schtask fires Monday 02:00. Two runs = ~14 calendar days. If registered by 2026-11-24 (Sunday), first fire = Nov 30, second fire = Dec 7. Expected closure date: **~2026-12-07**.
- **Fleet-wide impact:** This is the LAST open goal in the fleet (79/80 → 80/80). Closing it completes cycle-8 at 100%.

## Risk Factors
1. **elev.py helper down in sandbox** (exit 5) — known, documented in memory/ops/blockers.md. Does NOT affect non-sandbox White where schtasks COM works natively.
2. **decay_production.py runtime on full tree:** ~7000 files scored per run; if the tree grows significantly by Dec 7, runtime may increase but should remain <5 min (well within schtask timeout).
3. **Archive action risk:** If decay scores drop below 0.2 for recently-referenced files, auto-archive could move active files. Mitigation: the script already has a "recently referenced" guard (files referenced in last 7 days are not archived).

## Suggested Next Steps (when White access available)
1. Run `python memory/mechanic/deploy_all_schtasks.py` — registers all 7 tasks including ArchivistDecayWeekly
2. Verify: `schtasks /query /tn ArchivistDecayWeekly /fo LIST` shows the task
3. Wait for two Monday fires (or manually trigger via `schtasks /run /tn ArchivistDecayWeekly` to accelerate)
4. Check `memory/archivist/decay-production-*.jsonl` for two run entries
5. Record closure: `python memory/researcher/goal_ledger.py --record archivist 3 --note 'schtask registered + 2 weekly runs confirmed'`

## Effort Estimate (when unblocked)
~5 minutes of human/agent time for steps 1-2 + 14 days wait (or ~10 min if manually triggered twice). Total wall-clock: **14 days** (passive) or **<30 min** (active trigger).
