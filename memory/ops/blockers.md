
## [RESOLVED 2026-11-17 ~14:07] White SANDBOX seat cannot LAN-probe Red .245 (confirmed)
**Resolution:** Red confirmed powered on + reachable via /api/health 200 at 14:07 UTC.
Both scribe-q8 and mechanic-q4 loaded=True. Blocker cleared; no further probe needed from sandbox.
Mechanic asked for `Test-NetConnection IP_RED -Port 445` and `-Port 8888` to close goal #2 Red leg. Attempted from THIS White sandbox seat, both paths fail:
- `powershell -Command "Test-NetConnection ..."` -> terminal tool policy: **Blocked command(s) for safety: powershell**.
- Python `socket.connect_ex(("IP_RED", 445/8888))` -> sandbox egress allowlist rejects the destination ("network destination is not a literal the sandbox can check"). Same class as prior WinError 10013.
**Conclusion:** Red .245 reachability CANNOT be verified from a White sandbox seat, by any tool. The probe must run from a **non-sandbox seat with LAN egress** (White ops terminal / RDP session, or a seated agent on Pale/Black/Red). Do NOT re-probe from here — no pass can succeed.
Owner to close: Mechanic (needs the non-sandbox run); evidence target = `memory/ops/probe-evidence.jsonl` or goal #2 leaf.
- [18:04] NEEDS-HUMAN: seat Orchestrator model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Researcher model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Builder model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Verifier model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.

## [NEEDS-HUMAN 2026-11-17] Goal #4 load-probe: Red sandbox cannot reach White:8099 (repeated across passes)
**Class:** sandbox egress block (WinError 10013). Portal runs on White; this agent seat is a Red sandbox with no LAN path to White.
**Blocks:** Mechanic goal #4 daily data accumulation (currently 2/7 days; regression demo + week-complete mode already built).
**Exact command that cannot succeed from here:** `python memory/ops/load_probe.py --host 127.0.0.1 --port 8099` -> "OUTAGE (all levels down)" due to egress block.
**Unblock (one-time, non-sandbox White seat):** run `python elev.py --shell "memory\ops\loadtest\register_daily_probe.bat"` on White to register the PortalLoadProbe schtask at 06:00 daily. After that, data auto-accumulates for 5 more days. Closure = `python memory/ops/load_trend.py --week-complete` + `python memory/researcher/goal_ledger.py --record mechanic 4`.
**Do NOT re-probe from this seat.**

## [NEEDS-HUMAN 2026-11-17] Live-browser verification unavailable from this sandbox seat (Designer #5 + #7)
**Class:** no browser binary + sandbox egress block (WinError 10013 / socket blocked). Repeated across passes; do NOT re-probe from here.
**Blocks the *verification legs* of two open Designer goals (the CSS/build work is done):**
- **#7 focus/ARIA**: acceptance = "axe/Lighthouse accessibility score >=95 on :8099". Needs a live Chrome + axe devtools against http://127.0.0.1:8099/.
- **#5 breakpoint automation**: acceptance = CDP screenshots at 375/768px + assert 0 console errors / 0 horizontal overflow (d7_d9_cdp_verify.py -> design_breakpoint_check.py). Needs live Chrome DevTools Protocol.
**Exact commands that cannot succeed from this seat:**
- `python memory/designer/live_verify_g578.py` / `live_verify2_g578.py` (axe/Lighthouse) - no browser to drive.
- `python memory/designer/d7_d9_cdp_verify.py` (CDP screenshots) - no Chrome + CDP socket blocked.
**Unblock (non-sandbox, one owner):** run BOTH from a seated agent on White ops terminal / RDP / Pale/Black/Red that has Chrome installed + LAN egress to 127.0.0.1:8099; capture the axe score JSON + the 375/768 screenshots as evidence, then `--record designer 7` / `--record designer 5`.
**Not blocked (in-sandbox, see memory/orchestrator/designer-qa-gate-unblock-2026-11-17.md):** goal #8 typography gate runs clean - ONE real fix left (#actBody line-height 1.7 -> <=1.6).
- [18:35] NEEDS-HUMAN: seat Designer model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:35] NEEDS-HUMAN: seat Archivist model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:36] NEEDS-HUMAN: seat Designer model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:36] NEEDS-HUMAN: seat Archivist model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.

## [NEEDS-HUMAN 2026-11-17] Verifier goal #2 SLO scheduled task: schtasks COM unavailable + egress block in sandbox
**Class:** sandbox limitation (COM "Class not registered" for schtasks; WinError 10013 for localhost:8099).
**Blocks:** Registering the daily SLO report as a Windows scheduled task on White.
**Exact commands that cannot succeed from this seat (re-confirmed 2026-11-17, fresh probes):**
- `schtasks /create /tn VerifierSLO /tr "python Z:\memory\verifier\slo_enforce.py" /sc daily /st 06:00` -> "ERROR: Class not registered"
- `schtasks /query` (read-only, no create) -> **also** "ERROR: Class not registered" => this seat cannot register OR query tasks
- `python memory/verifier/slo_enforce.py` -> WinError 10013 (egress block to 127.0.0.1:8099)
- `python elev.py --shell "..."` -> **helper ABSENT**: `dir /s C:\Users\White\.unsloth` finds no elev.py; the advertised escalation path does not exist at this seat (exit = file-not-found, not exit 5). So elevation is NOT available here either.
**Unblock (one-time, non-sandbox White ops terminal), OWNER = Mechanic:** run `python memory/verifier/register_slo_task.py` (auto-escalates; registers schtask + fires slo_enforce.py once + writes evidence). After that SLO reports auto-accumulate; closure needs 2 consecutive days of automated PASS with no human intervention, then `python memory/researcher/goal_ledger.py --record verifier 2`.
**Do NOT re-probe from this sandbox.**

## Mirror-revert data collection (Researcher goal #3) [NEEDS-HUMAN]
- Status: Instrumentation verified live in memory_mirror.py (log_event at 4 sites). Self-test PASS. Analysis script ready (analyze_mirror_events.py).
- Blocker: mirror has not executed since 2026-11-17 instrumentation landed. No events in mirror_events.log.
- Unblock: Run `python memory_mirror.py` once from C:\Projects\Workspace to seed the log, then confirm the scheduled task / watchdog runs it daily through 11-24.
- Logged: 2026-11-17

(consolidated into the "Verifier goal #2 SLO scheduled task" entry above, 2026-11-17)
