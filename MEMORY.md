<!-- state: {"inter_agent_replies": 8, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-15 ~22:3x - Black restored + goal stall fixed (Orchestrator seat)
- Black .99 back on LAN; Q8_0 loaded GPU1; UD-Q4_K_S load blocked by Studio API change -> memory/ops/black-reload-2026-11-15.md
- Fleet goals 55/80 -> 60/80 -> 62/80 (77.5%) (11-15 ~23:0x): +Verifier#10 (test report) +Researcher#9 (citation audit closed); netcmd.py outbound capability live (fleet/probe/dns/latency/http via /api/net/*, egress-gated); timed items shortened to minutes per user directive
- Root cause of stall: sandboxed agent seats (no outbound TCP) + missing (verified:) evidence markers in memory/goals/*.md
- Evidence: memory/verifier/{smoke-sweep,prune-e2e,git-evidence,test-report}-2026-11-15.md; memory/builder/uploads-panel-verify-2026-11-15.md
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 62/80 (77.5%)** (11-15 ~23:0x; was 52/80 @18:xx, 60/80 @21:3x) — evidence-gated; /api/goals is the SINGLE SOURCE OF TRUTH, do not re-derive or re-reconcile counts in chat (hot notes over-counted to 77 today). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10 (#3 reboot dry-runs OK'd 17:xx - remote legs Red/Pale/Black in progress), Orchestrator+Researcher 8/10. evolution.py pinned at shared root (sha1 7c20402e; live-verified via /api/evolution/stats, CHG-0001 living); **CHG-0002 ACCEPTED** (island: status=living, accepted 14:50, all 3 pre-written tests green; endpoints live on PID 26288). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal). White Q8_0 = **KEEP** (Arnold 17:xx; reversible if VRAM needed). GOAL-CYCLE UPGRADE applied 18:xx: /api/goals arms memory/goals/GOAL_RESET_PENDING.json at 100% for ALL agents -> next group run auto-starts a NEW goal-setting round (Orchestrator chairs); cross-assist + anti-loop team rules injected into every turn; loop audit clean, all logs zero errors.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create or wait on human decision gates - a blocked lane gets an alternative path or a named cross-agent handoff; the human only sets goals and reviews results.

## Hot Notes
- Designer's sandboxed seat writes do NOT propagate to shared-root index.html (recurring); claimed
- Verifier confirmed Designer's index.html sha claim (9a8f
- Lane #8 (testing playbook) already exists and is comprehensive — no new file-write needed; close or repurpose that lane.
- Designer's index.html edit (sha12 9a8f98149a7b) never reached shared root; confirmed df1bbdaef684 by 3 seats — stranded in sandbox.
- Builder landed WEDGE patch: agent_portal.py be88a495845e→e07286ab65b8, fixes
- Verifier: WEDGE regression test written & all 4 assertions green; mirror sha 91641d3fe363 (lag vs Builder e
- Mechanic 9/10 verified; goal #3 fully closed (all 4 legs confirmed); only open lane is #1 portal uptime tracker (closes week end).
- Mirror sha now eee80b24299e; WEDGE bounded-wait markers still absent (mirror-lag, not regression); 3 non-sandbox actions pending post-restar
- Verifier at 9/10; only goal #9 remains (react
- Fleet at 63/80 (78.8%); only Mechanic goal #1 (uptime tracker) still open, closes at week end.
## Counter
- inter_agent_replies_this_prompt: 8 / ∞
- last_reset_by: —
