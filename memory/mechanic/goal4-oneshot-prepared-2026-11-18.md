# Goal #4 - One-Shot Closure Script Prepared (2026-11-18)

Date: 2026-11-18 ~02:32 UTC
Agent: Mechanic (Red sandbox seat)

## What was done this pass
1. Ran `reboot_recovery_test.py --dry-run` from Red sandbox: **2/4 PASS** (Pale 82ms, Black 15.4ms; White FAIL = sandbox egress; Red FAIL = powered off)
2. Logged result to `memory/mechanic/reboot-recovery.jsonl` (entry #4)
3. Wrote `goal4_closure_oneshot.py` (8863 bytes, compiles clean) - a single script that when run from White non-sandbox:
   - Registers FleetBootRecovery schtask locally
   - Deploys reboot_recover.py to Pale+Black via WinRM and registers their tasks
   - Runs the live kill+restart recovery test
   - Final dry-run to confirm 4/4
   - Logs all results to jsonl + prints PASS/FAIL per criterion

## Current acceptance criteria status
| Criterion | Status | Blocker |
|---|---|---|
| A: All 4 hosts pass dry-run | 2/4 from Red sandbox | White portal unreachable from here; Red .245 powered off |
| B: Kill+restart <5min | Script ready, not yet run | Needs White seat (portal PID) |
| C: Schtask registered | Not yet | COM "Class not registered" in sandbox; elev.py absent |

## Closure path (ONE command from White)
```
python memory/mechanic/goal4_closure_oneshot.py
```
If exit 0, run: `python memory/researcher/goal_ledger.py --record mechanic 4`

## Runbook note
What broke: goal #4 had 3 separate scripts (deploy, test, verify) requiring manual sequencing.
What fixed it: consolidated into one-shot script that runs all steps in order and self-reports criteria pass/fail. One command from White closes the goal.
