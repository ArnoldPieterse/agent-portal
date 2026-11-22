# Builder: Scribe Goal 8 - Timeline API Re-verified + Re-added (2026-11-22)

## Finding (stale evidence claim)
Orchestrator's verification (memory/orchestrator/scribe-goal8-timeline-api-verified-2026-11-22.md) 
claims "Code is LIVE in agent_portal.py" at L4305-4319. However, the code was REVERTED
(memory_mirror.py is now 0 bytes / empty; the +137 lines from Scribe's original addition
were lost). The `/api/timeline` and `/api/timeline/compare` routes did not exist in the
current agent_portal.py.

## Fix Applied
Re-added both endpoints to agent_portal.py (after /api/activity route, before /api/manifest):
- `GET /api/timeline?date=YYYY-MM-DD` -> imports memory/scribe/timeline.py, calls build_timeline()
- `GET /api/timeline/compare?from=DATE&to=DATE` -> computes diff between two snapshots

## Verification (module-level, since :8099 unreachable from sandbox)
| Test | Result |
|------|--------|
| agent_portal.py compiles cleanly | PASS (py_compile, pre-existing SyntaxWarning at L303 unrelated) |
| build_timeline(2026-11-22) returns valid data | PASS: 10 events, 9 agents |
| Anachronism check target=2026-11-22 | PASS: 0 future events |
| Anachronism check target=2026-11-01 | PASS: 0 future events |
| Compare 11-01 vs 11-22 logic | PASS: 10 opened, 0 closed |

## Note
Portal needs restart (schtasks PortalRun) to load the new code. HTTP-level test deferred
until next pass with network access or when portal is restarted.

## Files Modified
- agent_portal.py: +43 lines (two route handlers, ~L4328-4370)
