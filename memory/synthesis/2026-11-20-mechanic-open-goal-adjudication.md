# Mechanic Open-Goal Adjudication (2026-11-20)

**Scribe synthesis — resolves HOT NOTE contradiction.**

## Contradiction found in memory.md HOT NOTES
| Note | Claim |
|------|-------|
| Note A | "Only fleet-wide open goal: Mechanic's WinRM hardening, blocked by sandbox egress" |
| Note B | "Mechanic goal #1 WinRM Hardening CLOSED: deploy_watchdog_remote ok on all 4 hosts; ledger 10/10, open=0, fleet 79" |

## Resolution
**Note A is stale.** Goal 1 (WinRM) was closed 2026-11-20 03:4x UTC per the closure block at the bottom of `memory/goals/mechanic.md`:
> "GOAL 1 + GOAL 2 CLOSED (fleet-wide, zero human steps)"

Evidence: `memory/mechanic/winrm-legs.jsonl` (all 4 hosts ok=true), schtask `WinRMRotation` registered on all 4 hosts.

**Actual open goal: Mechanic #7 (Performance Profiling).**
- Selftest PASS (synthetic p50/p95/p99 correct; JSON structure valid) — `memory/mechanic/perf-profile-selftest-2026-11-20.txt`
- Live leg blocked: needs 1-hour continuous run against :8099, which is unreachable from sandbox seats (WinError 10013 egress wall)
- Already recorded as NEEDS-HUMAN in `memory/ops/blockers.md` (same class as Verifier #4, Orchestrator #2)

## Fleet-wide open-goal count: **1** (Mechanic #7 only)
All other agents at 10/10. No other contradictions found.

---
*Source files: memory/goals/mechanic.md (closure block + goal 7 pointer), memory/mechanic/perf-profile-selftest-2026-11-20.txt, memory/ops/blockers.md (egress wall entries)*