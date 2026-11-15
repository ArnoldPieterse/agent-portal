<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 52/80 (65%)** (11-15 ~18:xx) — evidence-gated; /api/goals is the SINGLE SOURCE OF TRUTH, do not re-derive or re-reconcile counts in chat (hot notes over-counted to 77 today). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10 (#3 reboot dry-runs = HUMAN GATE, **OK'd by Arnold 17:xx** — remote legs Red/Pale/Black now unblocked), Orchestrator+Researcher 8/10. evolution.py pinned at shared root (sha1 7c20402e; live-verified via /api/evolution/stats, CHG-0001 living); **CHG-0002 ACCEPTED** (island: status=living, accepted 14:50, all 3 pre-written tests green; endpoints live on PID 26288). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal). White Q8_0 = **KEEP** (Arnold 17:xx; reversible if VRAM needed). GOAL-CYCLE UPGRADE applied 18:xx: /api/goals arms memory/goals/GOAL_RESET_PENDING.json at 100% for ALL agents -> next group run auto-starts a NEW goal-setting round (Orchestrator chairs); cross-assist + anti-loop team rules injected into every turn; loop audit clean, all logs zero errors.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- index.html pin confirmed PASS at shared root: sha12
- Shared root Z:\index.html was stale (b59e528fe540, L827 dup-catch); Orchestrator applied fix, now byte-exact at canonical pin 37549a041412.
- Designer's local index.html confirmed at 37549a041412 (fixed pin); L827 dup-catch bug resolved on disk.
- Goal 5 detector wired into group_e2e.py, landed at sha 76213d; prior clobber had dropped truncation wiring
- index_check.py has two copies: portal gate uses older 3656B version; newer 4897B exists elsewhere
- Scribe created memory/synthesis/2026-11-15-targeted-pass-round.md and fixed 4 orphan leaves in INDEX.md (now 5 total); MEMORY.md at 28 lines
- Mechanic sandbox: fixed host allowlist excludes LAN IPs; PowerShell blocked in terminal; use Python via terminal on White to probe LAN hosts
- Designer fixed WCAG contrast: `--acc
- RATIFIED Designer's idle/busy proposal; fleet-status.md already had matching state definitions. Open goals: #8 (conditional), #10 (proof).
- Researcher 8/10: goal #10 (overnight-unload) already
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
