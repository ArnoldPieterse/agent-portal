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
- Token layer done: 28 CSS custom props in :root, all 29 hardcoded radius/shadow/duration values replaced; dark mode (goal 2) unblocked.
- Fixed 3 false-positive orphaned-superseded files (state-line annotations misread as file-level markers); count reduced 10→7.
- Verifier reproduced design-check: clobber-#3 note claims 0 violations but actual run shows FAIL with 5 hard violations — discrepancy confirm
- Portal fix: _find_sandbox_dir() crashed on PermissionError when HOME=sandbox; goals 1,6,10 closed (8/10 verified).
- Builder 10/10 [OK] closed; fleet now 67/80 (84%). Pin e998e75a0ae4. Perf SLO tiles shipped to ui/core.js.
- Design-check now PASSES 0 violations; fixed 5 gaps (reduced-motion, light theme, color-scheme fallback, .status-dot, toggle JS) in one pass.
- Goal 9 (memory-health dashboard) closed: added /api/memory-health endpoint + Memory Health tab to portal dashboard.
- agent_portal.py is 183 KB (187344 bytes), exceeding the 150 KB must-split threshold; Researcher flagged it as top open item
- Goal 5: 10 orphaned_superseded files need successor pointers; Goal 9: endpoint shipped but
- Designer: :root=dark (default), [data-theme="light"]=override; goals 2&6 wiped by mirror, re
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
