<!-- state: {"inter_agent_replies": 8, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 52/80 (65%)** (11-15 ~17:xx) — evidence-gated; /api/goals is the SINGLE SOURCE OF TRUTH, do not re-derive or re-reconcile counts in chat (hot notes over-counted to 77 today). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10 (#3 reboot dry-runs = HUMAN GATE, **OK'd by Arnold 17:xx** — remote legs Red/Pale/Black now unblocked), Orchestrator+Researcher 8/10. evolution.py pinned at shared root (sha1 7c20402e; live-verified via /api/evolution/stats, CHG-0001 living); **CHG-0002 ACCEPTED** (island: status=living, accepted 14:50, all 3 pre-written tests green; endpoints live on PID 26288). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal). White Q8_0 = **KEEP** (Arnold 17:xx; reversible if VRAM needed).

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- 11-15 evolution.py divergence RESOLVED: shared-root copy pinned sha1 7c20402e, live API verified. If a sandbox mirror shows a different sha, the mirror is stale — trust this pin.
- Mirror clobber still live for index.html/agent_portal.py (multiple shas observed across sandboxes). Rule: verify against shared-root pins, not local mirror reads; re-apply from pinned backups when clobbered.
- Arnold cleared all human gates 17:xx; Mechanic #3 reboot dry-runs (Red/Pale/Black) unblocked;
- RED reboot dry-run blocked: Windows Firewall on White blocks outbound to .2x (WinError 10013); PALE fixed via JWT; BLACK green.
- Designer local index.html is stale (b59e528fe540); canonical is 37549a041412 — sync
- Human gates cleared (Arnold 17:xx
- Archivist added missing ops INDEX pointer for mechanic-reboot-dryrun-remotes-2026-11-15.md (was absent from mirror).
- index.html pin confirmed PASS at shared root: sha12
- Shared root Z:\index.html was stale (b59e528fe540, L827 dup-catch); Orchestrator applied fix, now byte-exact at canonical pin 37549a041412.
- Designer's local index.html confirmed at 37549a041412 (fixed pin); L827 dup-catch bug resolved on disk.
## Counter
- inter_agent_replies_this_prompt: 8 / ∞
- last_reset_by: —
