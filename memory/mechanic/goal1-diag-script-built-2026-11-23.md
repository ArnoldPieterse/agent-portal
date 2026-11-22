# Goal #1 - Diagnostic Script Built (2026-11-23)

Date: 2026-11-23 (auto-loop pass)
Agent: Mechanic (White sandbox seat)

## What was done
Built `memory/mechanic/goal1_diagnose_fix.py` - a one-shot diagnostic + fix script
for the PortalLoadProbe schtask that stopped producing data after Nov 20.

## Script capabilities
1. Queries PortalLoadProbe LastRunTime + LastResult via schtasks /query
2. If task is missing, re-registers it (idempotent)
3. Manually triggers load_probe.py to backfill today's data
4. Verifies new entry appeared in load-baseline.jsonl
5. Counts unique days; if 7/7 reached, auto-runs --week-complete for closure verdict
6. Logs all steps to memory/mechanic/goal1-diag-<date>.jsonl

## Verification this pass
- py_compile: PASS (exit 0)
- Logic review: correct path resolution (HERE = project root), proper subprocess usage,
  idempotent (won't duplicate entries), graceful failure handling

## Deployment (one command from non-sandbox White seat)
```
python elev.py --shell "python memory/mechanic/goal1_diagnose_fix.py"
```

## Expected outcome on White
- If schtask stopped due to python path issue: re-registration fixes it
- If portal was down Nov 21-23: manual trigger backfills today (4/7 -> still need 2 more days)
- If portal is up and schtask works: data resumes automatically

## Status
Script built + compile-verified. Awaiting non-sandbox White seat for live execution.
This is the SAME blocker class as before (elev.py exit 5 in sandbox / COM unavailable),
already logged in memory/ops/blockers.md. Not re-probed.
