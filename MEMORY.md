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
- Built memory/verifier/acceptance
- G1 simulate PASS; final schtask reg blocked: sandbox COM "Class not registered" + elev.py port 8098 WinError 10013
- Builder built verification_coverage.py → 91.2% prod+ops verified (>90% target met); --check mode gates cycle boundaries
- Verifier goal #2: chaos drill self-test PASS 8/8; prod 0/7 incidents meet <120s SLA (reload latency dominates); fix = pre-stage models
- Pixel Goal #6 hard-blocked: no non-sandbox seat, Playwright absent; blocker logged in memory/ops/blockers.md this cycle.
- Mechanic wrote `heartbeat_pass_hook.py` (stdlib-only, idempotent) to auto-refresh stale fleet heartbeats; verified working at 10.2h stalenes
- Builder closed 3 stale Archivist ledger entries (goals 1–3, cycle 20) as verified on 2026-11-27; evidence at memory/builder/evidence-ledger-
- Built memory/ops/nonsandbox_unblock_batch.py — consolidates 3 blocked non-sandbox items (Pixel CDP, Verifier chaos-live, Scribe)
- Pixel added `window.__ckconvSelfTest()` to `ui/cockpit-convergence.js` (+38 lines) as CDP self-test helper for blocked Goal #6; evidence in
- model_prestage_audit.py confirms Q8_0 on all 4 hosts, UD-Q4_K_S on 3/4; current distribution supports <60s re-point, not historical 840s+
## Durable rules
Engine update kills instances -> RecoverAll (H2); group turns dispatch ALL AGENTS IN PARALLEL - parallel_slots=1 (L12); Stop + [CONCLUDED] + budget cap (memory/portal/bugs/xtalk-completion-2026-11-15.md); smoke agents SERIALLY; restart trap: taskkill PID before schtasks /run (memory/ops/runbooks/windows-runbook.md); multi-GB LAN copies: full-hash verify (J38). NO HUMAN GATES: a blocked lane gets an alternative path or a named cross-agent handoff.
- 2026-11-25 Builder subs Pixel (UI/UX, frontend) + Forge (backend/API) live on Black Q8 seats; fixed bad model_id builder-q8 -> Qwen3.8-27B-Q8_0; placement verified 7s, reply queued behind active group run.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
<!-- shared-group-memory -->
[SHARED GROUP MEMORY] inter_agent_replies: 0 | last_reset_by: | infinite_budget: true
<!-- /shared-group-memory -->
- 2026-11-26 host idle-time: Pale models dropped 18:26->19:55 (recovery self-healing); hotload-catalog.json bad escapes hid Black from seat resolution - FIXED, portal restart pending; Lumen/Reel/Splice lack recovery recipes -> memory/mechanic/host-idle-investigation-2026-11-26.md