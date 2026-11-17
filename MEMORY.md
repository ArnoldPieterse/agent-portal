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
- Scribe open-goal count corrected to 0 (auto-loop's "1 open" was stale); fleet now 62/80, Mechanic 6/10.
- All 5 open Mechanic goals share one root blocker: non-sandbox White session with working schtasks + LAN e
- Mirror sync reverts CSS token fixes (recurring, same pattern as TZ bug) — re-apply after each sync; 23 hex literals remain
- All 5 open goals blocked by same root cause (sandbox can't run schtasks); Mechanic built `batch_tier_b.py` with `--check` mode
- All 5 open goals blocked by one root cause: sandbox can't register schtasks; unblock = run consolidated script on White non-sandbox.
- Mechanic: 6/
- Mechanic's 4 open goals (#2,#4,#6,#8) all blocked by same sandbox root cause: schtasks COM unregistered + no SMB; do not re-probe, await Whi
- Mechanic wrote memory/mechanic/unblock-checklist-2026-11-18.md: one-shot runbook for all 5 open goals, all need non-sandbox White session
- Goal #4 (WCAG 2.1 AA a11y audit) CLOSED; skip-link + reduced-motion CSS re-applied after mirror-sync revert.
- Scribe terminal calls all failed ("tool call encountered an issue"); cycle-3 narrative append to memory/synthesis/cycle-narrative.md still o
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —

- 2026-11-17 13:5x ADMIN-BY-DEFAULT (user directive): every agent runs as admin, same as white. Elevated helper service built: elevated_helper.py (SYSTEM, 127.0.0.1:8098) + elev.py client + install_elevated_helper.bat (one UAC click). [SHELL] footer in agent_portal.py now tells all seats to route admin commands through `python elev.py ...` instead of giving up; takes effect on next portal restart. PENDING USER ACTION: double-click install_elevated_helper.bat once per host (files mirror to Pale/Black/Red automatically). Also fixed: agent_portal.py had 2 corrupted blocks (literal backslash-quote, syntax error) - repaired, compiles clean. Mechanic #4 load-test pipeline built + baseline captured (portal_loadtest.py, p95 ~60ms idle @8 workers). Designer (#6 status-dots, #2 dark mode) and Mechanic (#2 reboot-recovery dry-runs) tasks dispatched via /api/user-messages.