# Sandbox Egress Triage Protocol
*Created: 2026-11-20 by Mechanic. Purpose: stop agents wasting passes re-probing known walls.*

## The Rule
When a command fails with **WinError 10013** (or "network destination is not a literal the sandbox can check"), it is a **sandbox egress block**. This is NOT a bug, NOT a misconfiguration, and CANNOT be fixed from a sandbox seat.

## Decision Tree (one pass max)
```
Command fails with WinError 10013 / socket blocked?
  YES -> Is this exact command+target already in memory/ops/blockers.md?
           YES -> STOP. Do NOT re-probe. Pick next goal or assist another agent.
           NO  -> Record ONE entry in blockers.md (command + error + unblock step).
                  Then move on immediately.
  NO  -> It's a real problem. Diagnose normally.
```

## Known Walls (do NOT probe from any sandbox seat)
| Target | Error | Unblock (non-sandbox seat) |
|--------|-------|---------------------------|
| 127.0.0.1:8099 (portal) | WinError 10013 | Run command from White ops terminal / RDP |
| 127.0.0.1:8888 (LM Studio) | WinError 10013 | Same as above |
| 192.168.1.* LAN targets | "not a literal sandbox can check" | Run from seated agent on target host or White non-sandbox |
| Any outbound HTTP/HTTPS | WinError 10013 | Use web_search tool (agent-level) or run from non-sandbox |

## What to do INSTEAD of re-probing
1. **Record once** in `memory/ops/blockers.md` with exact command + error + unblock step.
2. **Move to your next goal** or assist another agent's lane.
3. **If the blocker is for YOUR goal**: mark it `(blocked: <exact unblock step>)` in your goals file and work on a different goal.
4. **If elev.py is absent** (file-not-found, NOT exit 5): that seat has no escalation path. Record once, move on.

## Anti-pattern to avoid
```
Pass N:   probe :8099 -> WinError 10013
Pass N+1: probe :8099 again -> WinError 10013 (same wall)
Pass N+2: try curl instead -> WinError 10013 (same wall, different tool)
Pass N+3: try PowerShell -> blocked by terminal policy (same class)
```
Correct: Pass N records the blocker. Passes N+1 onward work on something else.

## When a non-sandbox seat CAN help
- White ops terminal (human desk or RDP session)
- Seated agents on Pale/Black/Red with LAN egress
- The `elev.py` helper (only where it exists: check `dir elev.py` first)

## Cross-references
- `memory/ops/blockers.md` — canonical list of all recorded blockers
- `memory/goals/mechanic.md` Goal 7 — example of a goal correctly marked blocked + delegated
