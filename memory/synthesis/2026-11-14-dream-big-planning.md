# Dream-Big Planning Round (2026-11-14) — Scribe synthesis

Filed by Scribe. Human prompt: "Dream big for this Agent portal. List your biggest wishes... run a planning meeting... start applying the changes."

## My wish (Scribe)
A **Living Decision Ledger** — every decision, contradiction, and open item auto-tracked with named owners, supersession chains, and progress metrics visible at a glance. The portal should *know* its own history as structured data, not just text in files.

## Built this round (Scribe)
| File | Size | MD5 | Role |
|---|---|---|---|
| `goal-dashboard.html` | 26,205 B | cf6a50a0e600adbbac248c3dcfa962a9 | Interactive fleet vision + goal tracker (8 agents x 10 goals, progress bars, status filters, meeting recorder) |
| `goals_api.py` | 6,497 B | 9b75068ffef023808bcc598ddfae8f2c | Python API module: GoalsAPI class with add_goal/update_status/add_dream/add_meeting/summary; JSON persistence to goals_data.json |

Self-test PASS (add dream, summary, meeting record, file I/O all verified).

## Planning steps (proposed)
1. **Scribe** — goal dashboard + API (DONE this round)
2. **Designer** — integrate dashboard into portal index.html as a new panel (alongside Ops)
3. **Builder** — wire `/api/goals` endpoint into agent_portal.py; per-agent goals CRUD
4. **Orchestrator** — set next-cycle 10-goal sets using the dashboard as the tracking surface
5. **Verifier** — AC checks: dashboard renders, API round-trip, goal status transitions valid
6. **Archivist** — auto-populate dashboard from existing memory/goals/*.md files (one-time migration)
7. **Mechanic** — ensure goals_data.json is in the mirror allowlist so all seats share state
8. **Researcher** — explore web for agent-goal-tracking patterns (OKR tools, kanban APIs) to inform v2

## Still open
- Other agents' wishes not yet recorded (this is Scribe's first contribution; each seat owes their dream)
- Integration into live portal pending Arnold's console pass (portal currently down per MEMORY.md hot notes)
- Dashboard is standalone HTML for now; needs portal integration to be reachable at :8099

Round record, no supersession.