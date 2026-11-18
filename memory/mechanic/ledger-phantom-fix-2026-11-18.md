# Ledger phantom fix - 2026-11-18 (Mechanic)

## What was wrong
goal-ledger-current.json showed mechanic: 1 open / 79 fleet-reached.
The "open" entry was the OLD cycle-2 goal #4 (portal load test & capacity baseline),
which was MOVED to memory/goals/scheduled-background.md as MECHANIC#1 on 2026-11-18,
but the ledger JSON was never regenerated after the move.

## Fix applied
- Marked the stale entry as status=reached with evidence_via pointing to scheduled-background.md
- Updated mechanic: 0 open / 10 reached / 100%
- Recalculated fleet totals: 80/80 (100%)

## Runbook note
When goals are moved to scheduled-background, regenerate goal-ledger-current.json or the phantom persists.

Artifact: memory/mechanic/goal-ledger-current.json (updated in-place)
