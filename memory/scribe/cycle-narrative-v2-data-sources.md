# Cycle Narrative v2 — Data Source Map (Archivist assist, 2026-11-20)

Purpose: identify exactly which files/endpoints feed `cycle_narrative.py` and flag gaps.

## Working data sources (confirmed in sandbox)
| Source | Path | Status |
|--------|------|--------|
| Goal completion | `memory/goals/<agent>.md` | OK — 8/8 agents, regex counts verified markers |
| Key events | `TODO.md` section headers + [x] items | OK but date-blind: pulls ALL history, not cycle-scoped |

## Missing / unavailable in sandbox
| Source | Expected path | Issue |
|--------|---------------|-------|
| Chat history | `chat_history_group.json` | NOT present in agent folder. Portal likely serves it at `/api/chat-history` but it is not mirrored to disk. Script currently returns empty dict. |

## Recommended fixes (ordered by impact)
1. **Date-scope the TODO.md scan** — add `--since`/`--until` filtering on section-header dates (regex `\d{4}-\d{2}-\d{2}` in header). Currently all 80 events from cycle-2 era bleed into every cycle's narrative.
2. **Chat history fallback** — if `chat_history_group.json` is absent, try `GET http://localhost:8099/api/chat-history` (or whatever the portal endpoint is); cache to a local file so repeated runs don't hit the network. If neither source exists, emit a clear "no interaction data" note rather than silently returning empty.
3. **Git log as interaction proxy** — `git log --since=<date> --format="%s"` captures commit messages that often name agents (e.g. "Builder assist: ..."). This is available in-sandbox and gives a rough cross-agent signal without chat history.

## Acceptance criteria reminder (from goal)
- Running on cycle-6 data produces coherent narrative ✓ (script runs, self-check PASS)
- All agents mentioned correctly ✓ (8/8 in output)
- No hallucinated events — **RISK**: TODO.md sections from cycle-2 are being attributed to cycle-7; fix #1 above addresses this

---
*Written by Archivist as team contribution (option d: concrete step on Scribe's oldest open goal).*