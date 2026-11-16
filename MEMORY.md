<!-- state: {"inter_agent_replies": 1, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-15 ~22:3x - Black restored + goal stall fixed (Orchestrator seat)
- Black .99 back on LAN; Q8_0 loaded GPU1; UD-Q4_K_S load blocked by Studio API change -> memory/ops/black-reload-2026-11-15.md
- Fleet goals 55/80 -> 60/80 -> 62/80 (77.5%) (11-15 ~23:0x): +Verifier#10 (test report) +Researcher#9 (citation audit closed); netcmd.py outbound capability live (fleet/probe/dns/latency/http via /api/net/*, egress-gated); timed items shortened to minutes per user directive
- Root cause of stall: sandboxed agent seats (no outbound TCP) + missing (verified:) evidence markers in memory/goals/*.md
- Evidence: memory/verifier/{smoke-sweep,prune-e2e,git-evidence,test-report}-2026-11-15.md; memory/builder/uploads-panel-verify-2026-11-15.md
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET CYCLE 2: 20/80 (25%)** (11-16 ~16:xx) - Orchestrator+Researcher sets COMPLETED ON THEIR BEHALF (user directive; their models stay unloaded on White): O 8/10 + R 8/10 verified, 4 time-gated progress goals open. C1-C4 contradiction queue drained (synthesis/2026-11-16-contradiction-rulings.md); C2 ratifies Designer#4 (tokens live at pin 2c6399f2d853). Model-load governance live in portal code (GET /api/models/status; pre-run flag) - restart pending to load. FLEET FINDINGS: Black .99 :8888 DOWN (Builder+Verifier seats); Red :8099 filtered from White (scoped, not blanket); Q4_K_S 128 vs Q8_0 82 tok/s. /api/goals = SSOT.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create or wait on human decision gates - a blocked lane gets an alternative path or a named cross-agent handoff; the human only sets goals and reviews results.

## Hot Notes
- Goal 8 pre-fill: 62%→95% (61/64) after signal-based owner-inference; passes ≥80 bar; accuracy check on inferred owners still open.
- Goal 1 (CI gate) COMPLETED: all 4 suites pass; sse_parse.py created as standalone SSE module extracted from group_e2e.py
- Goal 3 done: 25 inline styles → named classes in index.html; pin e0679e5f→c0629a5b
- evolution.py subprocess.run lacks explicit cwd; nested sandbox processes lose working dir — fix: add cwd="." to those calls
- Goal 7 (focus rings + ARIA landmarks
- Verifier confirmed 8/10 goals verified & batch-re-recorded after mirror cycle wiped ledger; Goals 9-10
- Portal restart PENDING:
- Goal 7 (focus rings + ARIA landmarks) COMPLETED: universal :focus-visible rule in index.html, all interactive elements covered.
- Mirror cycles repeatedly clobber the goal ledger; evidence files survive on disk,
- Builder has evidence files on disk for all 10 goals but never ran --record; ledger shows 0/10. Mirror cycles keep
## Counter
- inter_agent_replies_this_prompt: 1 / ∞
- last_reset_by: —
