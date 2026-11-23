# Autonomy Loop-Closure Rate Report
Generated: 2026-11-23T00:31:16Z

## Summary
- Total autonomous actions tracked: **104**
- CLOSED (detected -> action -> verified): **90**
- OPEN (in progress / not yet verified): **8**
- FAILED (loop closed but outcome negative): **6**
- **Overall loop-closure rate: 86.5%**
- Decision-log closure rate: 41.7%

## Per-Type Breakdown (decision-log entries)
| Type | Closed | Open | Failed | Total | Closure% |
|------|--------|------|--------|-------|----------|
| SELFTEST | 1 | 0 | 0 | 1 | 100% |
| oom_recovery | 0 | 2 | 0 | 2 | 0% |
| playbook_complete | 2 | 0 | 0 | 2 | 100% |
| playbook_dry_run | 1 | 0 | 0 | 1 | 100% |
| playbook_rollback | 0 | 0 | 1 | 1 | 0% |
| playbook_step | 5 | 0 | 1 | 6 | 83% |
| runbook_execution | 1 | 0 | 4 | 5 | 20% |
| unknown | 0 | 6 | 0 | 6 | 0% |

## Goal Ledger Breakdown
- Goals reached (closed): **80**
- Goals open: **0**
- Goal closure rate: 100.0%

## Interpretation
Loop-closure rate is HEALTHY (>=80%). Most autonomous actions complete their full loop.
