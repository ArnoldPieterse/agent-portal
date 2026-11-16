# HOTLINE escalation protocol v2 (Orchestrator goal #8, set 2026-11-16)

Replaces ad-hoc hotline notes. One-line format; 5-minute ack SLA from any seat; no human gates (standing rule).

## Triggers (any one fires the line)
| Code | Trigger | Example seen |
|------|---------|--------------|
| H-OUT | Host or portal down / unreachable where expected | Red :8099 timeout/filtered while :8888 open (2026-11-16, C3) |
| H-MODEL | Agent model not loaded / seat dead | Orchestrator+Researcher 404 "downloaded but not loaded" (2026-11-16 goal round) |
| H-WEDGE | Run silent >90s with GPU idle or journal mtime frozen | g-1a1e312535-a23478 11-15 17:52 |
| H-DATA | Clobber / data loss / served!=disk detected | F-VER-01 (index.html served-root non-reproduction, 11-15) |
| H-GOAL | Goal-cycle machinery failure (flag corruption, collection incomplete) | GOAL_RESET_PENDING truncated to 0 bytes by NameError (2026-11-16) |

## Format (one line in TODO.md top section + jsonl event)
`H-CODE | host/agent | one-line fact + measured evidence | owner | ack-by (5 min)`

## Log (events since v2 adopted 2026-11-16 ~15:1x)
- H-MODEL | White / Orchestrator+Researcher | both seats 404 not_loaded; single tensor-split llama-server (PID 33560 :57451) alive but untracked by Studio routing; group rounds loop on auto-resume without a chair | Orchestrator (governance shipped: pre-run flag + /api/models/status) | ack same-turn (this line is the ack); user directive: skip loading, seat-drafted goals cover lanes
- H-OUT | Red 192.168.1.245 | portal :8099 timeout/filtered (1502ms) while Studio :8888 open (2.9ms) + SMB 445/139 open — scoped, not blanket | Mechanic (check if Red portal process is running; scoped fix only) | ack due next round
- H-GOAL | White / portal | GOAL_RESET_PENDING.json corrupted by pre-fix NameError in start_group_run consumption | Orchestrator seat | FIXED same-day: code fixed (rid before use, serialize-before-truncate), flag repaired with true consumed record, commit 9d89362 + auto-syncs

## Rules
1. Every H-line gets an owner and an ack-by; unacked >5 min = escalate to the next round's first cross-talk.
2. Evidence before escalation: measure once from a non-sandbox seat where possible (C3 lesson).
3. No looping on a blocked line: if the fix is not one action, document + move on (user directive) and keep the line open in the risk register instead.
