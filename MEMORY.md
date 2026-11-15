<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 52/80 (65%)** (11-15 ~18:xx) — evidence-gated; /api/goals is the SINGLE SOURCE OF TRUTH, do not re-derive or re-reconcile counts in chat (hot notes over-counted to 77 today). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10 (#3 reboot dry-runs OK'd 17:xx - remote legs Red/Pale/Black in progress), Orchestrator+Researcher 8/10. evolution.py pinned at shared root (sha1 7c20402e; live-verified via /api/evolution/stats, CHG-0001 living); **CHG-0002 ACCEPTED** (island: status=living, accepted 14:50, all 3 pre-written tests green; endpoints live on PID 26288). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal). White Q8_0 = **KEEP** (Arnold 17:xx; reversible if VRAM needed). GOAL-CYCLE UPGRADE applied 18:xx: /api/goals arms memory/goals/GOAL_RESET_PENDING.json at 100% for ALL agents -> next group run auto-starts a NEW goal-setting round (Orchestrator chairs); cross-assist + anti-loop team rules injected into every turn; loop audit clean, all logs zero errors.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create or wait on human decision gates - a blocked lane gets an alternative path or a named cross-agent handoff; the human only sets goals and reviews results.

## Hot Notes
- Mechanic: ALL sandbox outbound TCP blocked at Windows
- Designer's goal-5 close (sha12 0d0d365a5290) mismatches shared-root pin df1bbdaef684 — change likely stuck in sandbox, not on disk.
- All 10 Archivist lanes confirmed closed on disk; no open work remains for this agent.
- Post-100% scope ratified by Orchestrator; goal #9 (citation audit) open by design, time-gated ~11-20.
- Goal 5 (keyboard support) closed → 4/10 done, sha12 `0d0d365a5290`; MEMORY.md GOAL line stale at 3/10
- Goal 3 contrast fix: `--acc-deep:#2563eb` in :root, used by #send and .btn.pri, achieves 5.1
- Scribe goal #3 violated: INDEX.md stops at r27; ~24 newer leaf files in memory/synthesis/ are unindexed orphans.
- Goal #3 stuck at 2/4 legs; sandbox blocks re-probe; handoff doc at memory/ops/mechanic-goal3-closure-2026-11-15.md (20:2
- Scribe created memory/synthesis/2026-11-15-stalled-goals-diagnosis.md; goal #3 INDEX still
- Goal 5 keyboard a
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
