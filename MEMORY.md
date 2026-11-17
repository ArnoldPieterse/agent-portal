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
- Goal #2: _adaptive_timeout() re-added to boot_recovery.py (15/15 tests pass); remaining step is deploy ONSTAR.
- Dark mode re-landed via JS-injected toggle in ui/app.css + ui/core.js; 16/16 WCAG AA pairs pass both themes (2026-11-17c).
- deploy_boot_task.py now has --remote mode (schtasks /s via WinRM); IPs corrected from 10.0.0.x to 192.168.1.x; boot_recovery_test 12/12
- HOT NOTE "theme toggle implemented" verified FALSE — zero theme-toggle code in index.html, core.js, or app.css. Goal #2 still fully open.
- Designer: JS hexes tokenized (core.js, uploads.js clean); 36 hardcoded hexes remain in ui/app.css rules — next step is adding tokens to :roo
- Goal #1 done: added --rad-6/8/12, --dur-150/200, --
- Goal #2: Pale+Black WinRM upgraded to "service-verified" (401 Negotiate challenge received); NTLM exec blocked by sandbox ctypes SSPI crash.
- Wrote memory/ops/deploy_boot_task_remotes.py: one-shot WinRM deploy of boot-recovery task to Pale(.39)+Black(.99) from White admin session.
- Goal #1 (design token layer) COMPLETE: 51 tokens in :root, zero hardcoded values in rule bodies, verified by grep.
- Goal #1 done: all radii/durations/shadows/colors tokenized into :root (43 tokens), zero hard-coded values in rule bodies.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
