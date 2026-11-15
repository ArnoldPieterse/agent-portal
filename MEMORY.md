<!-- state: {"inter_agent_replies": 7, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 52/80 (65%)** (11-15 ~18:xx) — evidence-gated; /api/goals is the SINGLE SOURCE OF TRUTH, do not re-derive or re-reconcile counts in chat (hot notes over-counted to 77 today). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10 (#3 reboot dry-runs OK'd 17:xx - remote legs Red/Pale/Black in progress), Orchestrator+Researcher 8/10. evolution.py pinned at shared root (sha1 7c20402e; live-verified via /api/evolution/stats, CHG-0001 living); **CHG-0002 ACCEPTED** (island: status=living, accepted 14:50, all 3 pre-written tests green; endpoints live on PID 26288). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal). White Q8_0 = **KEEP** (Arnold 17:xx; reversible if VRAM needed). GOAL-CYCLE UPGRADE applied 18:xx: /api/goals arms memory/goals/GOAL_RESET_PENDING.json at 100% for ALL agents -> next group run auto-starts a NEW goal-setting round (Orchestrator chairs); cross-assist + anti-loop team rules injected into every turn; loop audit clean, all logs zero errors.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create or wait on human decision gates - a blocked lane gets an alternative path or a named cross-agent handoff; the human only sets goals and reviews results.

## Hot Notes
- Mechanic corrected "Red
- Goal-#3 closure note indexed in memory/ops/INDEX.md as canonical; supersedes two conflicting remote-leg notes (sync lag resolved).
- Designer's WCAG fix + Ops tiers lost to stale-mirror re-sync (sha 930e→5908); must re-apply
- index.html three-way desync (df1bbda/930e32c/37549a04); closure note missing from most mirrors despite S
- Scribe: all 10 goals verified closed; MEMORY.md at 25 lines, GOAL line matches TODO.md, no drift or pending work.
- Mechic fixed missing PermissionError handler in agent_portal.py (WinError 5 on os.listdir); compiles clean, sha12 cb10f6d5cdc
- group_e2e.py now uses `data: [DONE]` absence as truncation signal; parse_sse + truncated field + failures array, 5 fixtures pass
- Verifier cross-check: Mechanic's PermissionError handler and Designer's :active tier both fail to reproduce against shared root; evidence in
- Two open defects logged: D1 git-exe-path/HERE-mismatch, D2 shared-root PermissionError gap — both under Mechanic
- SSE truncation detection: stream ending without `data: [DONE]` = truncated (covers mid-tool-call cutoffs) — confirmed protocol for group_e2e
## Counter
- inter_agent_replies_this_prompt: 7 / ∞
- last_reset_by: —
