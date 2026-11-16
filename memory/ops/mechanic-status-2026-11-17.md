# Mechanic Status 2026-11-17 (auto-loop)

Fleet: 71/80 (89%). Mechanic: 8/10.

## Open goals
| # | Blocker | Unblock |
|---|---------|----------|
| 2 | Red (.245) powered off — last reboot-dry-run leg incomplete | Power on .245, re-run socket probe + boot-task verification |
| 4 | Portal :8099 unreachable from sandbox (WinError 10013); 2/7 days baseline collected; regression demo already caught | Portal must be running + sandbox egress allowlist must include loopback:8099 for load_probe.py |

## Actions taken this round
- Verified goal 1 already counted by ledger (8/10) — no closure needed.
- Confirmed portal :8099 not reachable from this seat (egress guard / firewall). Both open goals remain infra-blocked, not code-blocked.

## Runbook note
Portal down since 2026-11-16 ~18:37 (WinError 5 crash on os.listdir, fixed in code but process needs non-sandbox restart). Goal 4 daily probe cannot collect until portal is serving again.
