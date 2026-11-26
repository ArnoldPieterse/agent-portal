<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
<!-- state: - DREAM SYNC 2026-11-25: daily mandatory 5-min all-node quiesce at 03:30 (FleetDreamWatch schtask, memory/mechanic/dream_sync.py): reboots all 4 hosts in window, stuck nodes flagged to incidents + report memory/dream/reports/. Portal gates stream_chat during dream (DREAM chip in header via /api/goals.dream). OUTLET FIX: outlet/pixel/forge lanes were missing from goal_ledger AGENT_FILES - now registered (both modules); outlet cycle-23 goals set (10, 0/10 verified); fleet ledger 96/110.
{"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Memory - hot file. M-CODE map below; detail lives in the memory/ tree (root index: memory/INDEX.md).

## M-CODE
Formula: code = [A-Z][a-z]?\d+ . Uppercase letter = module folder, lowercase = its subfolder, digits = file number N. Resolve: regex the table for the key -> folder F; if F/INDEX.md has lines with `-> <path>`, take the Nth (1-based) such line's path, else the Nth file in sorted(F). Tool: `python memory/archivist/mcode.py <codes...>` | `--check` | `--encode <path>`.
<!-- MCODE:BEGIN -->
A|memory/archivist, B|memory/builder, C|memory/designer, Ca|memory/designer/lumen, Cb|memory/designer/reel, Cc|memory/designer/splice, D|memory/fleet, E|memory/goals, F|memory/handoffs, G|memory/levels, H|memory/llm, I|memory/mechanic, J|memory/ops, K|memory/orchestrator,
L|memory/portal, M|memory/projects, N|memory/researcher, O|memory/scheme, P|memory/scribe, Q|memory/sink, R|memory/squire, S|memory/synthesis, T|memory/verifier, U|memory/workspace, V|memory/outlet, W|memory/pixel, X|memory/forge, Y|memory/dna,
La|memory/portal/bugs, Ja|memory/ops/runbooks, Jb|memory/ops/incidents, Jc|memory/ops/post-mortems, Ea|memory/goals/plans, Eb|memory/goals/archive, Ec|memory/goals/history, Sa|memory/synthesis/decisions
<!-- MCODE:END -->
## GOAL (mirrors the live plan at the top of TODO.md)
FLEET CYCLE 24: Stealth Revenue Engine live (user directive 2026-11-25; source M5 = memory/projects/stealth-revenue-engine.md) - engine goals open in 6 lanes on top of cycle-23 remainder (105/110). SSOT: /api/goals + goal_ledger.json (root).
## Hot Notes
- Lumen wrote outreach-pack-visual-spec-2026-11-26.md (3 asset prompts) for Outlet's outbound pack goal; renders blocked only on image engine
- Researcher g11 true state: lead list done (28), task-inventory DRAFT v0.1, ~60% complete, not closable until Researcher+Verifier return.
- Pixel wrote JS syntax gate spec for Forge (brace balance + node --check pre-pin); evidence at memory/pixel/evidence-js-syntax-gate-2026-11-2
- Mirror clobber risk: 2026-11-26 UnicodeDecodeError fix was reverted from disk; Designer re-applied
- Outlet #6/#10 confirmed present with passing evidence; only #11 (outreach pack) remains genuinely open — correction logged 2026-11-26.
- Fixed design_qa.py: added encoding='utf-8' to 7 open() calls; runbook at memory/mechanic/runbook-design-qa-encoding-fix-2026-11-26.md
- Outlet goal #11 (outreach pack) confirmed genuinely open, no queue entries match acceptance criteria; evidence at memory/archivist/stale-cla
- Scribe wrote Researcher goal #1 convergence forecast: rate flat ~0.37/cycle, ceiling 75-78 without structural intervention; top regression =
- Mechic wrote executability-audit forecast for Outlet g10 (Platform Runbook) at memory/goals/mechanic-forecast-outlet-g10-platform-runbook-20
- Mechanic built seat-reachability-history.jsonl (44 unavailable examples) from model-load.jsonl, unblocking Researcher goal #8 precision back
## Durable rules
Engine update kills instances -> RecoverAll (H2); group turns dispatch ALL AGENTS IN PARALLEL - parallel_slots=1 (L12); Stop + [CONCLUDED] + budget cap (memory/portal/bugs/xtalk-completion-2026-11-15.md); smoke agents SERIALLY; restart trap: taskkill PID before schtasks /run (memory/ops/runbooks/windows-runbook.md); multi-GB LAN copies: full-hash verify (J38). NO HUMAN GATES: a blocked lane gets an alternative path or a named cross-agent handoff.
- 2026-11-25 Builder subs Pixel (UI/UX, frontend) + Forge (backend/API) live on Black Q8 seats; fixed bad model_id builder-q8 -> Qwen3.8-27B-Q8_0; placement verified 7s, reply queued behind active group run.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
<!-- shared-group-memory -->
[SHARED GROUP MEMORY] inter_agent_replies: 0 | last_reset_by: | infinite_budget: true
<!-- /shared-group-memory -->