<!-- state: {"inter_agent_replies": 3, "last_reset_by": "", "infinite_budget": true} -->

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
- Archivist goal 2: index_check.py shipped & working but pre-prune wiring unconfirmed; 324/441 orphan rate logged
- Builder at 5/10 goals; open: #2 SMB mirror round-trip, #5 group_e2e.py truncation flag, plus 3 more not yet shown
- Verifier goal #4 (daily health check) blocked: sandbox cannot reach localhost TCP; needs Orchestrator or egress-enabled seat to run.
- Designer: index.html in shared folder hashes df1bbdaef684 (not 418a57eec190) — no rebase needed; deployment blocked on egress, patch
- Builder at 7/10 verified; goal #8 testing playbook confirmed complete (110 lines, all PASS), now working goal #9 architecture.md
- Designer v3 patch at `designer/index-patched-v3.html` (1256 lines); deploy blocked by sandbox egress, needs Mechanic/Builder with network ac
- Fleet verified at 62/80 (77
- Mechanic's Z:\ sandbox seat has zero outbound network (4 paths tested: python localhost/127.0.0.1, curl, powershell all blocked); needs non-
- Builder closed #5 (6
- Verifier closed goal #5 (bug repro) — all 10/10 goals now verified; evidence at memory/verifier/bug-repro-and-finding-2026-11-16.md
- 2026-11-16 goal sweep (user-directed): fleet 80/80 closed - builder#5,8,9,10; designer#3,4,5,7,8,9,10 (pin advanced to 2c6399f2d853: D4 --sp-*/--fs-* tokens + D7 breakpoints, CDP 0 console errors); mechanic#1 uptime >=99.98%; researcher#9 final audit 5/5 live; verifier#5 repro log. See memory/goals/*.md verified notes.

## Counter
- inter_agent_replies_this_prompt: 3 / ∞
- last_reset_by: —
