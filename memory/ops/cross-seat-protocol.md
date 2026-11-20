# Cross-Seat Coordination Protocol
**Owner:** Orchestrator | **Created:** 2026-11-20 (cycle-8 goal #7)
**Purpose:** Structured handoff of blocked work between agent seats so no lane stalls on a seat-specific limitation.

## When to use
An agent's goal is blocked by a **seat-specific limitation**:
- Sandbox egress wall (WinError 10013 / socket block to localhost or LAN)
- Missing helper binary (elev.py absent or helper down, exit 5)
- COM unavailable (schtasks "Class not registered")
- File absent in sandbox (canonical lives on a non-sandbox host)

Do NOT use for: model-unreachable (auto-resolves via hotload), code bugs, design decisions.

## Handoff file format
Path: `memory/ops/handoffs/<agent>-<goal#>-YYYY-MM-DD.md`

```markdown
# HANDOFF: <Agent> Goal #<N> — <short title>
**From:** <agent name> (seat: <hostname>)
**To:** <target agent or "any non-sandbox seat"> 
**Date:** YYYY-MM-DD
**Class:** <egress-wall | elev-helper-down | com-wall | file-absent | other>

## Blocker (one line)
<exact error message or condition>

## Exact unblock command
```
<the single command that, when run from the correct seat, resolves this>
```

## Evidence target
<path where success evidence will appear>

## Status
[OPEN]  <- target seat updates to [RESOLVED YYYY-MM-DD <evidence-ref>] when done
```

## Rules for the target seat
1. **Pick up on your next pass.** If a handoff file addressed to you (or "any non-sandbox seat") exists and is [OPEN], execute its unblock command as your first action.
2. **Record evidence** at the stated path, then update the handoff file's Status line to `[RESOLVED <date> <ref>]`.
3. **If the command fails**, append a `## Retry` section with the new error; do NOT delete the file. After 2 failed retries, escalate back to Orchestrator for re-triage.

## Rules for the source agent
1. Write the handoff file ONCE when the blocker is confirmed (not on first probe — confirm it's a genuine seat limitation).
2. Log the same class in `memory/ops/blockers.md` (one line) so the fleet dashboard sees it.
3. Do NOT re-probe the blocked command from your own seat on subsequent passes.
4. Your goal stays OPEN until the target seat marks the handoff [RESOLVED].

## Resolution tracking
Orchestrator sweeps `memory/ops/handoffs/` each cycle:
- Any [OPEN] handoff older than 3 days gets a reminder ping in auto-loop.
- At cycle end, all handoffs should be [RESOLVED]; unresolved ones carry to next cycle with a note.

## Cycle-8 inventory (created 2026-11-20)
| Handoff file | From | To | Class | Status |
|---|---|---|---|---|
| orchestrator-1-2026-11-20.md | Orchestrator | any non-sandbox seat | elev-helper-down | OPEN |
| verifier-4-2026-11-20.md | Verifier | any non-sandbox White seat | egress-wall | OPEN |
| mechanic-4-2026-11-20.md | Mechanic | any non-sandbox White admin seat | com-wall | OPEN |
