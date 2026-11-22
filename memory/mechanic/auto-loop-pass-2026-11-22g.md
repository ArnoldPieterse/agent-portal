# Mechanic auto-loop pass 2026-11-22g

## Action taken
Built `white_seat_closure_run.py` (207 lines, compile PASS) - one-command script that closes all 4 remaining open goals (#1, #2, #3, #4) from a non-sandbox White session in a single execution.

Phases:
- Phase 0: Pre-flight (schtasks COM + :8099 + LAN egress checks)
- Phase 1: Register schtasks via deploy_all_schtasks.py (goals #1, #2, #7)
- Phase 2: Live CB 200-with-down test against /api/fleet/status (goal #4)
- Phase 3: WinRM E2E anti-stall test against Black (goal #3)
- Phase 4: Verify data accumulation in load_trend.jsonl + mirror-repairs.jsonl (goals #1, #2)

Auto-records closures via goal_ledger.py when all phases pass.

## Current state of open goals
| Goal | Status | Unblock |
|------|--------|----------|
| #1 Load Test | 1/7 days in sandbox; schtask registered on White Nov 17 (per blockers.md RESOLUTION) but data stopped at Nov 20 | Run white_seat_closure_run.py from White |
| #2 Mirror Heal | Same as #1 | Same |
| #3 WinRM E2E | Black:5985 reachable from sandbox; no pywinrm + no PowerShell in sandbox | Same (Phase 3) |
| #4 Fleet CB | Built + unit-tested; live leg needs :8099 | Same (Phase 2) |

## Blocker (unchanged, NOT re-probed)
All 4 goals require non-sandbox White seat. Single unblock command:
```
python memory/mechanic/white_seat_closure_run.py
```
This replaces the prior scattered "run X from White" notes with one entry point.

## Files created
- memory/mechanic/white_seat_closure_run.py (new, 207 lines, py_compile PASS)