# Goal 5: Slip-Risk Endpoint - Built + Verified 2026-11-18

## What was built
- `_slip_risk_snapshot()` function in `agent_portal.py` (inserted after `_goals_snapshot`)
- Route `/api/goals/slip-risk` wired into `do_GET`
- Scoring: weighted sum 0.4*p_by_agent + 0.3*p_by_type + 0.3*p_by_depth from `slip_prediction_table.json`
- Risk levels: HIGH >= threshold (0.87), MEDIUM >= threshold*0.7, LOW below

## Verification
- Syntax check passes (py_compile)
- Inline test with 7 agents produces differentiated scores (LOW/MEDIUM/HIGH)
- Ledger marker recorded via `goal_ledger.py --record orchestrator 5`

## Remaining for full acceptance
- Live browser render check (amber/red dots in goals UI panel) - requires portal running + hard-refresh
