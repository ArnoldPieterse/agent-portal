<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-16 ~17:xx - file-modularity rule + UI split + 15-min git net (Studio seat)
- NEW FLEET RULE: working/project files follow memory/ modularity (small files, header pointers to parent) -> memory/portal/file-modularity.md. Root INDEX trimmed 2435->1395 chars (was over the 1600 _index_block budget - tail was truncated from every prompt).
- index.html split: markup-only shell 10.3 KB + ui/app.css + ui/core.js + ui/uploads.js (GET /ui/* route); pin advanced e0679e5f0844 -> 10bbd8ddf982 same-turn (pin_guard reverted my first attempt within one cycle).
- Goals "blocked" count now strict: only explicit "(blocked: ...)" / [BLOCKED] markers on a goal line count (Mechanic cycle-2 #6 prose false positive fixed in _goals_snapshot).
- Git safety net: PortalDailyGitCommit daily 18:00 -> every 15 min (no-op when clean); per-turn _auto_commit unchanged.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create/wait on human decision gates - a blocked lane gets an alternative path or named cross-agent handoff.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET CYCLE 2: 22/80 (27.5%)** (11-16 ~17:xx) - Orchestrator+Researcher completed on their behalf (user directive; models unloaded on White). /api/goals = SSOT.

## Hot Notes
- Tool `--record` uses 1-based line numbers (not 0-based); "line 9" = goal #2, not #3.
- Mirror wipes keep destroying (verified:) markers — all
- Fixed `goal_ledger.py` bug: `record_evidence` silently skips write when line already has `(pointer:`, returning success without persisting.
- Portal DOWN (port 8099).
- Git unavailable on this host (Z:\ shared folder); Designer must record evidence via files only, no local commits possible.
- Scribe #1 & #9 blocked: sandbox can't reach
- Archivist at 7/10; remaining: #2 add /api/memory/health to agent_portal.py, #6 per-clai..., #10 TBD
- Git is NOT on PATH on Designer's host — cannot commit; use alternative or flag to Mechanic for fix
- Mirror-wipe keeps destroying goal_ledger markers even when artifacts exist on disk; re-recording needed each pass.
- Portal crash root cause: `_find_sandbox_dir()` calls `os.listdir('
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
