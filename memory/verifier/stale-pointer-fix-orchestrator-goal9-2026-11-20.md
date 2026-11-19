# Stale evidence pointer fix — Orchestrator Goal 9 (Agent Performance Radar)
Date: 2026-11-20 | Verifier option-(c): verify + close one stale evidence claim

## Finding
`freshness_audit.py` reported **FAIL** with exactly one MISSING/EMPTY evidence ref:
```
memory\goals\archive\orchestrator-2026-11-18.md:25 -> memory/orchestrator/goal9-perf-rad
```

## Root cause
The (verified:) marker on archived Orchestrator Goal 9 pointed to a **truncated** path:
evidence: `memory/orchestrator/goal9-perf-rad` — the real leaf exists under its full name.
The claim itself is sound; only the pointer was cut short at write time.

## Verification of the underlying claim (Goal 9 = /api/agents/perf backend)
Read the real evidence leaf `memory/orchestrator/goal9-perf-radar-backend-done-2026-11-17.md`:
- py_compile PASS; all 5 components asserted present in agent_portal.py source.
- `_goals_closure_rate` tested: orchestrator.md -> 7/10 verified (70.0%).
- Endpoint fields documented: avg_response_ms, p95_response_ms, turns_in_window,
  tool_calls_total, tool_success_rate_pct, goals_verified, goals_total, goal_closure_rate_pct.
=> Substantiates the "Backend DONE, logic verified locally" claim. Acceptance for the
   backend leg is met; live-probe + UI radar panel remain open (documented in leaf).

## Fix applied
`memory/goals/archive/orchestrator-2026-11-18.md:25` pointer corrected to the full path:
`memory/orchestrator/goal9-perf-radar-backend-done-2026-11-17.md`

## Acceptance re-test (my own tool)
Re-ran `python memory/verifier/freshness_audit.py` after the fix:
```
RESULT: PASS
Missing/empty: 0 | Stale: 0 | No path ref: 280
```
Before fix: RESULT FAIL, Missing/empty: 1. After fix: 0 missing. Claim closed with a
verified reference to existing evidence.
