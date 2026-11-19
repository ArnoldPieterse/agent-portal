<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-18 - all host passwords are EMPTY (RDP + SMB, Arnold)
- RDP and SMB passwords are empty on every host (White/Red/Pale/Black); remote accounts: Red/pale/black. Detail: memory/ops/host-port-task-map-2026-11-15.md #access-rdp--smb--all-hosts.

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
- uploads.js has 3 remaining warning glyphs in textContent contexts; inline SVG won't work there without DOM refactoring (goal 8 blocker).
- /api/fleet/status implemented in agent_portal.py; live verification still open (host-gated), UI strip is separate work item
- Fleet status code confirmed present (lines 1090–4179
- Goal 5: notifications.js exists but not loaded in index.html; calls UI.icSVG (real
- Goal 8 Tier-A verified in-tree; code lives on Red and must be applied to White via non-sandbox queue before live probe.
- RECALL: - **M1** (`memory/goals/archive/researcher-2
- Goal #5: notifications.js calls non-existent `UI.icSVG`; real API is `UI.icon
- Goal 8 `_fleet_status` patch verified local but Red sandbox has NO remote-apply path to White; escalated NEEDS-H
- Designer found UI.icSVG is non-existent; correct API is UI.icon
- Goal 8 fleet_status code confirmed in agent_portal.py (L1090,4209) + ui/core.js (L414); live check blocked by WinError 10013; patch pending
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —

- 2026-11-17 13:5x ADMIN-BY-DEFAULT (user directive): every agent runs as admin, same as white. Elevated helper service built: elevated_helper.py (SYSTEM, 127.0.0.1:8098) + elev.py client + install_elevated_helper.bat (one UAC click). [SHELL] footer in agent_portal.py now tells all seats to route admin commands through `python elev.py ...` instead of giving up; takes effect on next portal restart. PENDING USER ACTION: double-click install_elevated_helper.bat once per host (files mirror to Pale/Black/Red automatically). Also fixed: agent_portal.py had 2 corrupted blocks (literal backslash-quote, syntax error) - repaired, compiles clean. Mechanic #4 load-test pipeline built + baseline captured (portal_loadtest.py, p95 ~60ms idle @8 workers). Designer (#6 status-dots, #2 dark mode) and Mechanic (#2 reboot-recovery dry-runs) tasks dispatched via /api/user-messages.