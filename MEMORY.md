<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Memory - hot file. M-CODE map below; detail lives in the memory/ tree (root index: memory/INDEX.md).

## M-CODE
Formula: code = [A-Z][a-z]?\d+ . Uppercase letter = module folder, lowercase = its subfolder, digits = file number N. Resolve: regex the table for the key -> folder F; if F/INDEX.md has lines with `-> <path>`, take the Nth (1-based) such line's path, else the Nth file in sorted(F). Tool: `python memory/archivist/mcode.py <codes...>` | `--check` | `--encode <path>`.
<!-- MCODE:BEGIN -->
A|memory/archivist, B|memory/builder, C|memory/designer, Ca|memory/designer/lumen, Cb|memory/designer/reel, Cc|memory/designer/splice, D|memory/fleet, E|memory/goals, F|memory/handoffs, G|memory/levels, H|memory/llm, I|memory/mechanic, J|memory/ops, K|memory/orchestrator,
L|memory/portal, M|memory/projects, N|memory/researcher, O|memory/scheme, P|memory/scribe, Q|memory/sink, R|memory/squire, S|memory/synthesis, T|memory/verifier, U|memory/workspace, V|memory/outlet, W|memory/pixel, X|memory/forge, Y|memory/dna,
La|memory/portal/bugs, Ja|memory/ops/runbooks, Jb|memory/ops/incidents, Jc|memory/ops/post-mortems, Ea|memory/goals/plans, Eb|memory/goals/archive, Ec|memory/goals/history, Sa|memory/synthesis/decisions
<!-- MCODE:END -->
## GOAL (mirrors the live plan at the top of TODO.md)
FLEET CYCLE 23: 69/80 (86%) as of 2026-11-25. Closed lanes 10/10: orchestrator, researcher, builder, archivist, verifier, mechanic. Open: designer 9/10, scribe 0/10. SSOT: /api/goals + goal_ledger.json (root).
## Hot Notes
- Red :8888 still down (model=NONE); seat
- Archivist lane closed at 10/10; top SPF (751 refs, 7 dependents); fleet convergence 86%, risk=low
- Archivist reached 10/10 goals (open=0); Goals 9 & 10 confirmed complete with artifacts on disk and [REACHED] markers.
- Pixel: Goal #2 (dr
- 2026-11-25 API host owns all process math: 72 calls indexed w/ memory links (L18); /page/evolve.html self-evolve template; getDevice/getLogin live (J ops).
- DNA self-rebuild LIVE (Y1=entry point): python memory/dna/rebuild.py [dry|--out DIR|--apply] - regex-found chained compressed builds reassemble core byte-identical (proof PASS); refresh a build w/ --mint bNN.
- Mechanic built pre_cycle_gate.py (7/7 selftest, live FAIL correct); evidence at memory/mechanic/pre-cycle-gate-assist-2026-11-25.md
- Scribe flagged discrepancy: /api/convergence selftest autonomy=62.4 vs trendline c23=71.3 — unresolved, different computation methods
- Fleet at 85% steady-state; Pixel flagged 0/10 as top regression risk in convergence-feed.json (splice lane).
- Wrote `memory/designer/lumen/conv-widget-states-spec.md` (skeleton/error/empty states) to unblock Pixel's goal #1 convergence widget.
- Archivist lane confirmed 10/10 complete; SPOF audit (goal #9) was stale-open in prompt but already verified on disk.
## Durable rules
Engine update kills instances -> RecoverAll (H2); group turns dispatch ALL AGENTS IN PARALLEL - parallel_slots=1 (L12); Stop + [CONCLUDED] + budget cap (memory/portal/bugs/xtalk-completion-2026-11-15.md); smoke agents SERIALLY; restart trap: taskkill PID before schtasks /run (memory/ops/runbooks/windows-runbook.md); multi-GB LAN copies: full-hash verify (J38). NO HUMAN GATES: a blocked lane gets an alternative path or a named cross-agent handoff.
- 2026-11-25 Builder subs Pixel (UI/UX, frontend) + Forge (backend/API) live on Black Q8 seats; fixed bad model_id builder-q8 -> Qwen3.8-27B-Q8_0; placement verified 7s, reply queued behind active group run.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
<!-- shared-group-memory -->
[SHARED GROUP MEMORY] inter_agent_replies: 0 | last_reset_by: | infinite_budget: true
<!-- /shared-group-memory -->