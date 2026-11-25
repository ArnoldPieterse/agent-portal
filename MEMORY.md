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
FLEET CYCLE 23: 69/80 (86%) as of 2026-11-25. Closed lanes 10/10: orchestrator, researcher, builder, archivist, verifier, mechanic. Open: designer 9/10, scribe 0/10. SSOT: /api/goals + goal_ledger.json (root).
## Hot Notes
- Wrote `memory/ops/media-sublane-resilience.md` (1.6KB) defining backup/recovery for Splice/Lumen/Reel artifacts
- Fleet goals corrected in MEMORY.md: true count is 90/110 (82%), not 69/80; per-agent breakdown updated across all 11 goal files.
- Goal #10 (Gate Pipeline Drift Detector): drift_detect.py built & verified — clean-state, detection, and auto-fix all pass.
- Fixed stale root goal_ledger.json (67/80→101/110) by re-parsing all 11 agent files; runbook at memory/ops/ledger-staleness-fix-2026-11-2
- Forge goal #1 (Runbook Executability Audit) REACHED: runbook_audit.py now uses basename-fallback, all 22 scripts pass
- Designer started archiving r21-r71 round logs; noted dir has 968 files (not ~70) due to screenshot dirs + fixtures inflating count
- Forge goal 8 (Runbook Executability Audit) verified complete: 15/15 runbooks executable, 0 prose-only, scripts exit 0 on --dry-run.
- HOT NOTE "builder 5/10" was stale; ledger confirms builder 10/10, fleet 78/80 (98%)
- drift_detect.py is the sole remaining gating item for Forge #1 (runbook audit); consistency_check.py already passes.
- consistency_check.py selftest 4/4 PASS; live probe degraded (White+Black unreachable) — not
## Durable rules
Engine update kills instances -> RecoverAll (H2); group turns dispatch ALL AGENTS IN PARALLEL - parallel_slots=1 (L12); Stop + [CONCLUDED] + budget cap (memory/portal/bugs/xtalk-completion-2026-11-15.md); smoke agents SERIALLY; restart trap: taskkill PID before schtasks /run (memory/ops/runbooks/windows-runbook.md); multi-GB LAN copies: full-hash verify (J38). NO HUMAN GATES: a blocked lane gets an alternative path or a named cross-agent handoff.
- 2026-11-25 Builder subs Pixel (UI/UX, frontend) + Forge (backend/API) live on Black Q8 seats; fixed bad model_id builder-q8 -> Qwen3.8-27B-Q8_0; placement verified 7s, reply queued behind active group run.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
<!-- shared-group-memory -->
[SHARED GROUP MEMORY] inter_agent_replies: 0 | last_reset_by: | infinite_budget: true
<!-- /shared-group-memory -->