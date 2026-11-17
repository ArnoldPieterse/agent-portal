<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-16 ~17:xx - file-modularity rule + UI split + 15-min git net (Studio seat)
- NEW FLEET RULE: working/project files follow memory/ modularity (small files, header pointers to parent) -> memory/portal/file-modularity.md. Root INDEX trimmed 2435->1395 chars (was over the 1600 _index_block budget - tail was truncated from every prompt).
- index.html split: markup-only shell 10.3 KB + ui/app.css + ui/core.js + ui/uploads.js (GET /ui/* route); pin advanced e0679e5f0844 -> 10bbd8ddf982 same-turn (pin_guard reverted my first attempt within one cycle).
- Goals "blocked" count now strict: only explicit "(blocked: ...)" / [BLOCKED] markers on a goal line count (Mechanic cycle-2 #6 prose false positive fixed in _goals_snapshot).
<279 chars of arguments you sent, already written to MEMORY.md; elided to save room. Not tool output; the file on disk holds it.>
- AUTO-LOOP (user request): idle agents re-enter the work queue within ~1 min - _autoloop_watchdog solo passes,
  UMQ-first priority, streak cap 40 -> memory/ops/autoloop.md

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); group turns dispatch ALL AGENTS IN PARALLEL - White's Studio only queues same-host agents internally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on destination disk, never size+magic (ops/probes.md). NO HUMAN GATES (Arnold 11-15): agents never create/wait on human decision gates - a blocked lane gets an alternative path or named cross-agent handoff.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET CYCLE 2: 22/80 (27.5%)** (11-16 ~17:xx) - Orchestrator+Researcher completed on their behalf (user directive; models unloaded on White). /api/goals = SSOT.

## Hot Notes
- deploy_boot_task.py UNC IPs corrected: 10.0.0.x → 192.168.1.x; boot_recovery_test.py passes
- All 21 token pairs pass WCAG AA contrast; reusable audit script saved for Goal #10 regression gate.
- Goal #2 (dark mode): light tokens in ui/app.css done + WCAG AA verified; remaining = toggle button in index.html + screenshot pair.
- Fixed deploy_startup_folder.py: create_vbs() leaked Python string-concat into VBS output; rewrote with .format() + quote-doubling.
- Theme toggle implemented: button in index.html, localStorage+prefers-color-scheme logic in core.js; only screenshot pair remains for Goal #2
- Dark mode + theme toggle done: light tokens in app.css (WCAG AA), toggle btn in index.html, JS in core.js; pin at 207ba077f4d6
- Light-theme `--faint` fixed to #6672
- Goal #2: _adaptive_timeout() re-added to boot_recovery.py (15/15 tests pass); remaining step is deploy ONSTAR.
- Dark mode re-landed via JS-injected toggle in ui/app.css + ui/core.js; 16/16 WCAG AA pairs pass both themes (2026-11-17c).
- deploy_boot_task.py now has --remote mode (schtasks /s via WinRM); IPs corrected from 10.0.0.x to 192.168.1.x; boot_recovery_test 12/12
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
