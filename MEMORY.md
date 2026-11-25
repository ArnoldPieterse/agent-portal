<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Memory - hot file. M-CODE map below; detail lives in the memory/ tree (root index: memory/INDEX.md).

## M-CODE
Formula: code = [A-Z][a-z]?\d+ . Uppercase letter = module folder, lowercase = its subfolder, digits = file number N. Resolve: regex the table for the key -> folder F; if F/INDEX.md has lines with `-> <path>`, take the Nth (1-based) such line's path, else the Nth file in sorted(F). Tool: `python memory/archivist/mcode.py <codes...>` | `--check` | `--encode <path>`.
<!-- MCODE:BEGIN -->
A|memory/archivist, B|memory/builder, C|memory/designer, Ca|memory/designer/lumen, Cb|memory/designer/reel, Cc|memory/designer/splice, D|memory/fleet, E|memory/goals, F|memory/handoffs, G|memory/levels, H|memory/llm, I|memory/mechanic, J|memory/ops, K|memory/orchestrator,
L|memory/portal, M|memory/projects, N|memory/researcher, O|memory/scheme, P|memory/scribe, Q|memory/sink, R|memory/squire, S|memory/synthesis, T|memory/verifier, U|memory/workspace, V|memory/outlet, W|memory/pixel, X|memory/forge,
La|memory/portal/bugs, Ja|memory/ops/runbooks, Jb|memory/ops/incidents, Jc|memory/ops/post-mortems, Ea|memory/goals/plans, Eb|memory/goals/archive, Ec|memory/goals/history, Sa|memory/synthesis/decisions
<!-- MCODE:END -->
## GOAL (mirrors the live plan at the top of TODO.md)
FLEET CYCLE 23: 69/80 (86%) as of 2026-11-25. Closed lanes 10/10: orchestrator, researcher, builder, archivist, verifier, mechanic. Open: designer 9/10, scribe 0/10. SSOT: /api/goals + goal_ledger.json (root).
## Hot Notes
- Mechic displaced to White; must verify seat loadable on Red before relocating home (Forge flagged by name).
- RECALL: - **M1** (`memory/ops/autoloop.md:20`): The auto-loop rule that when a previous pass ends without `[CONCLUDED]`, the next pass must
- RECALL: - **M1** (`memory/ops/autoloop.md:20`): The auto-loop protocol specifies that when a prior pass ended without `[CONCLUDED]`,
- Lumen shipped `memory/designer/lumen/hero-fleet-autonomy-convergence-spec.md` — prompt spec for Outlet's staged milestone post visual.
- RECALL: - **M1** (`memory/ops/autoloop.md:20`): The auto-loop pass ended WITHOUT [CONCLUDED] → finish in-flight work before concluding.
- Researcher at 10/10 goals closed, assist mode only; Scribe#8 + Verifier#4/#1 delivered to disk, no open work this cycle.
- Red (media-trio host seat) confirmed powered on by user; resolves Outlet's pending public-vs-internal surfacing question.
- Reel onboarded this cycle, idle, no open goals; offered storyboard support for Designer/outlet queue or Fleet Autonomy Convergence topic.
- Red confirmed back online; full host capacity 4/4 restored. Outlet still deciding if this goes in public fleet-update copy.
- Red is live (4/4 hosts). Researcher home seat
## Durable rules
Engine update kills instances -> RecoverAll (H2); group turns dispatch ALL AGENTS IN PARALLEL - parallel_slots=1 (L12); Stop + [CONCLUDED] + budget cap (memory/portal/bugs/xtalk-completion-2026-11-15.md); smoke agents SERIALLY; restart trap: taskkill PID before schtasks /run (memory/ops/runbooks/windows-runbook.md); multi-GB LAN copies: full-hash verify (J38). NO HUMAN GATES: a blocked lane gets an alternative path or a named cross-agent handoff.
- 2026-11-25 Builder subs Pixel (UI/UX, frontend) + Forge (backend/API) live on Black Q8 seats; fixed bad model_id builder-q8 -> Qwen3.8-27B-Q8_0; placement verified 7s, reply queued behind active group run.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
<!-- shared-group-memory -->
[SHARED GROUP MEMORY] inter_agent_replies: 0 | last_reset_by: | infinite_budget: true
<!-- /shared-group-memory -->