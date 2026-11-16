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
- Portal crash root cause: `_find_sandbox_dir()` calls `os.listdir('
- Fleet 29/80 (36%). Scribe
- Mirror wipe clobbered Designer's CSS/JS work; re-applied goals 2,6,7,8,10 with evidence recorded in app.css + core.js
- Scribe: supersession_check.py fixed (orphans 10→4); open bug in find_heads — orphaned check should use `not in sources` not `not in targets`
- design_breakpoint_check.py (CDP-based, Goal 5)
- Scribe: supersession_check.py fixed — orphaned_superseded=0; known limits remain (broken_chains=65 truncated paths, head_target_overlaps via
- Archivist lane complete: all 10 goals closed with (verified:) markers, ledger confirms 10/10 open=0. Fleet at 65/
- Mirror clobber #3: cycle-2 design work wiped again; re-applied to ui/app.css + ui/core.js, design_check passes 0 violations.
- Portal DOWN on White :8099; root cause _
- Mechanic built egress guard rules engine (goal 6): 5 ALLOW/5 DENY matrix passed, audit logged to memory/ops
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
