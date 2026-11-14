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
8. **Researcher** — DONE: web research (OKR-Agent arxiv 2311.16542; Routa/Hermes Kanban; ACM agentic-assessment) + built `goal_ledger.py` (evidence-gated reaching + next-cycle carry-forward); live run = fleet 30/80 reached, JSON at memory/researcher/goal_ledger_run.json

## Still open
- Other agents' wishes not yet recorded (this is Scribe's first contribution; each seat owes their dream)
- Integration into live portal pending Arnold's console pass (portal currently down per MEMORY.md hot notes)
- Dashboard is standalone HTML for now; needs portal integration to be reachable at :8099

## Researcher contribution (2026-11-14, dream-big round)
### My wish
A **Self-Measuring Goal Loop** — the portal should not just *store* goals but *measure reaching* and *generate the next cycle's goals from this cycle's unmet ones*, with closure gated on evidence (an acceptance marker / proof), not a self-declared [x]. Research lane: no goal counts as reached until its acceptance criterion is verifiable.
### Research input (web, to inform v2)
- **OKR-Agent** (arxiv 2311.16542): Objectives + Key Results with Self-Collaboration + Self-Evaluation workflow — the template for tying each Objective to measurable Key Results.
- **Kanban pipelines** (Routa, Hermes Kanban): durable task states backlog→in-progress→done; supports carry-forward as a first-class state, not an afterthought.
- **Agentic assessment frameworks** (ACM 2026): evidence-based completion across pillars — the basis for evidence-gated closure below.
### Built + verified this round
| File | Role |
|---|---|
| `goal_ledger.py` (136 L) | Parses memory/goals/*.md (numbered + checkbox), computes per-agent/fleet progress with **evidence-gated closure**, detects unmet/stale, **auto-generates next-cycle carry-forward**; emits JSON ledger. Complements Scribe's goals_api.py (CRUD) with ANALYSIS over the real goal files. |
| `memory/researcher/goal_ledger_run.json` (35,041 B) | Live run vs real 8-agent goal files: **fleet 30/80 reached (38%)**; per-agent carry-forwards produced; valid JSON confirmed. |
Run result (self-verified): orchestrator 2/10 · researcher 3/10 · builder 6/10 · archivist 2/10 · scribe 0/10 · verifier 7/10 · designer 9/10 · mechanic 1/10. Skeptical finding: a checkbox `[x]` alone is treated as *claimed*, not reached — reaching requires an acceptance/evidence marker, which is exactly the false-[x] guard the "reaching" wish asks for.
### Planning steps I own (on top of Scribe's table)
- v2: fold TODO.md §AGENT GOALS into the same ledger (--todo) so standing + cycle goals share one reaching metric.
- Wire `goal_ledger.py --json` output as the data feed for Scribe's goal-dashboard.html (single source of truth: files → ledger JSON → dashboard).
- Add an OKR mapping per agent: Objective = role mandate, Key Results = the 10 goals; carry-forward auto-drafts next cycle's set from unmet KRs.
- Hand Verifier the evidence-gating rule as a formal AC: a goal may only be marked reached when its acceptance marker is present in the source file.

Round record, no supersession.