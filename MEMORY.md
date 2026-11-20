<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->

## 2026-11-19 - design-token deep sweep complete (White direct)
- All UI files clean: 0 hardcoded hex (outside var() fallbacks), 0 real glyph chars, 0 raw px font-size across ui/*.js + index.html + app.css; all var() refs resolve to tokens; node --check passes 9/9. Evidence: memory/designer/deep-sweep-2026-11-19.md (commit 85e3097). Headless Edge CDP does not work in this sandbox - use static verification for UI acceptance.

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
- xref_monitor.py baseline: 6917
- Goal 10 open: QA script hardcodes stale 5-step type scale; live tokens.css has 8 tokens (11–24px). Fix: derive from tokens.css, not duplicat
- Auto-loop prompt "open" counts are consistently stale; always trust goal_ledger over loop trigger numbers.
- Fixed extract_decisions.py --since bug: was clobbering decisions.jsonl; now merges+dedups on normalized text. Evidence in goal1-incremental-
- Scribe Goal 7 (Archive Navigation Index) verified complete; Scribe now 3/10 per ledger update 2026-11-20.
- Designer confirmed 10/10 goals reached; pivoted to assist Scribe's Cross-Agent Handoff Protocol (Scribe was at 2/10).
- Fixed data-loss bug in extract_decisions.py: --since mode now merges with existing entries instead of clobbering
- Mechanic 10/10 closed; auto-loop "2 open" is stale — winrm_pool_selftest 20/20 PASS, no action needed
- xref baseline post-compaction: 1811 files, 44
- Goal 9 gap: actRender & mergeQueueLoad use plain-text empty states, not UI.emptyState() — needs fixing for full panel coverage.
## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —

- 2026-11-17 13:5x ADMIN-BY-DEFAULT (user directive): every agent runs as admin, same as white. Elevated helper service built: elevated_helper.py (SYSTEM, 127.0.0.1:8098) + elev.py client + install_elevated_helper.bat (one UAC click). [SHELL] footer in agent_portal.py now tells all seats to route admin commands through `python elev.py ...` instead of giving up; takes effect on next portal restart. PENDING USER ACTION: double-click install_elevated_helper.bat once per host (files mirror to Pale/Black/Red automatically). Also fixed: agent_portal.py had 2 corrupted blocks (literal backslash-quote, syntax error) - repaired, compiles clean. Mechanic #4 load-test pipeline built + baseline captured (portal_loadtest.py, p95 ~60ms idle @8 workers). Designer (#6 status-dots, #2 dark mode) and Mechanic (#2 reboot-recovery dry-runs) tasks dispatched via /api/user-messages.