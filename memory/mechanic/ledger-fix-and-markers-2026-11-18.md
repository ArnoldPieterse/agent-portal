# Mechanic pass 2026-11-18 (ledger fix + marker re-application)

## Actions
1. **goal_ledger.py bug fixed**: `record_evidence()` was skipping writes when a line contained `(pointer:` anywhere in it. Fixed to check marker type independently — verified markers now write correctly alongside existing pointers.
2. **Verified markers re-applied** to memory/goals/mechanic.md for goals #3, #5, #9, #10 (all had prior closure evidence; markers were lost after a previous pass, likely mirror revert cycle).

## Result
- Dashboard: Mechanic 4/10 reached (was showing fewer due to missing markers)
- Remaining open (6): #1, #2, #4, #6, #7 (Tier-B), #8
- All remaining goals blocked on non-sandbox access (elev.py absent at Red seat; NEEDS-HUMAN already logged in blockers.md)

## Runbook note
goal_ledger.py `record_evidence()` line 290: changed from `if "(pointer:" not in lines[hit] and "(verified:" not in lines[hit]` to per-marker-type check so verified markers can coexist with pointer markers on the same line.
