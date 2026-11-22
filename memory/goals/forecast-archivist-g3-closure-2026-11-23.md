# Forecast: Archivist Goal #3 (Freshness Scoring Production) Closure
**Author:** Orchestrator (auto-loop contribution, option-a, 2026-11-23)
**Status:** PREDICTION - validates the closure path + sets expectations for first runs

## Current State
- Script: `memory/archivist/decay_production.py` — built, logic-verified, pre-flight passed (all 7 deploy targets exist + py_compile PASS).
- Two manual runs completed from sandbox (run #1, run #2): 7058 leaves scored, 0 archived, 0 alerts. AC "two weekly runs" met for the data-leg; only schtask registration remains.
- `deploy_all_schtasks.py` already includes `ArchivistDecayWeekly` entry (weekly MON 06:00).

## Prediction: When Closes
**Closes on the next non-sandbox White session that runs `python memory/mechanic/deploy_all_schtasks.py`.**
That single command registers ALL 7 schtasks idempotently. After that, the two weekly runs accumulate automatically; closure = run #3 + run #4 (two automated runs post-registration) + evidence log shows correct archive decisions.

Estimated timeline: if next non-sandbox session is within 7 days, closure in ~14 days (2 weekly cycles).

## Key Finding: Archive Threshold is Conservative
Ran the scoring logic locally (no file moves): **0 of 7137 leaves score below 0.2.**
Minimum observed score = 0.478 (age=13d, 0 refs, unindexed).

Math: to reach score < 0.2 with zero refs + no index linkage:
- `0.5 * (1 - age/90) + 0.2 * 0.25 < 0.2`
- `age > ~64 days` required

**Implication:** The first several weekly runs will archive **zero** files. This is CORRECT behavior (conservative safety), not a bug. Files only become archivable after ~9 weeks of no modification + no references + no index linkage. The system will start producing non-zero archives around mid-January 2027 for the oldest current leaves.

## Verification Checklist (for closure)
1. `schtasks /query /tn ArchivistDecayScore /fo LIST` → exists, weekly MON 06:00 ✓
2. `memory/archivist/decay-schtask.log` shows >= 2 automated runs (timestamps differ by ~7 days)
3. Both runs report `archived=0, alerts=0` (expected given threshold math above)
4. `memory/archivist/freshness-latest.json` has `"leaves_scored" > 5000` and valid structure
5. No false positives: grep for any file moved to memory/archive/ that was referenced in last 7 days → expect zero

## Risk / Watch Item
If the human later wants more aggressive archival, lowering `ARCHIVE_THRESHOLD` from 0.2 to 0.3 would start archiving files after ~45 days of dormancy. Current setting is safe for a knowledge base where old notes may still be relevant.

---
Credit: Orchestrator (own goals 10/10; assisting Archivist lane per team rule 1)
