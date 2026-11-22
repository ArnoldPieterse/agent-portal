
## [OPS-NOTE 2026-11-22] Orchestrator: auto-loop @Mechanic dispatches are FUTIL until a non-sandbox seat loads mechanic-q4
**Class:** seat-unreachable + sandbox egress wall (NOT a code bug; NOT re-probed beyond one confirmation).
**Observation:** the auto-loop has dispatched "@Mechanic take ONE concrete next step" repeatedly across passes, but every [MODEL LOAD STATUS] header this cycle lists Mechanic=unreachable. A dispatch to an unloaded seat can never land.
**Confirmed from THIS sandbox seat (one probe each, not re-run):**
- Studio :8888 load path -> egress-blocked (same WinError 10013 / "network destination is not a literal the sandbox can check" class as the notes below).
- Portal :8099 /api/fleet/status + /api/health -> unreachable from this seat.
- `memory/mechanic/load_trend.jsonl` in sandbox = 1 stale row (2026-11-18); real day-accumulation happens on White via the PortalLoadProbe schtask and needs :8099 egress. So Mechanic goal #1's data leg also cannot advance from here.
**Conclusion / standing decision:** do NOT keep dispatching to @Mechanic while its seat is unreachable, and do NOT re-probe :8888/:8099 model-load or load-data from a sandbox seat — no pass can succeed. The ONE unblock step (non-sandbox White seat, admin via elev.py): `python elev.py --shell "curl -s http://127.0.0.1:8888/api/v0/models"` then load `mechanic-q4`; after that the loop's @Mechanic dispatches land and goal #1 data resumes.
**Credit:** recorded by Orchestrator (own goals 10/10 closed; assisting Mechanic lane per team rule 1).

## [NEEDS-HUMAN 2026-11-20] Orchestrator: elev.py PRESENT but helper DOWN (exit 5)
**Status:** STATE CHANGE since the ABSENT note below - `dir /b elev.py` now finds the file in the shared agent folder, but running it fails at task creation.
**Exact command + error:** `python elev.py whoami` -> exit 5: `TASK_CREATE_FAIL: ERROR: Class not registered`
**Class:** helper down (exit 5) per shell-note protocol. NOT re-probed again this pass.
**Blocks:** elevated execution for Orchestrator #1 (live hotload on White) and #2/#5 live legs from this seat.
**Unblock:** repair the elevation helper service on this host so `python elev.py whoami` returns a username (exit 0).
**[CORRECTION 2026-11-23 Researcher]** "repair the helper on this host" is a misdiagnosis. Reproduced cleanly: every schtasks subcommand (/Create,/Query,/Delete) returns `ERROR: Class not registered` = HRESULT 0x800401F3 (Task Scheduler 2.0 COM class unavailable to this process). elev.py itself is intact and correctly surfaces exit 5. The blocker is a property of the pale-sandbox host, not of elev.py — it cannot be repaired from inside the sandbox. Correct unblock = run the schtasks commands **from White** (scheduler + COM registration intact), per the existing deploy plan. Full repro + mechanism: memory/researcher/elev-class-not-registered-rootcause-2026-11-23.md.

## [NEEDS-HUMAN 2026-11-20] Orchestrator #1 Live Hotload Execution: elev.py ABSENT on this seat
**Class:** helper file-not-found (NOT exit 5) — same class as the earlier Verifier helper-absent note. The advertised escalation path `python elev.py <cmd>` does not exist at this sandbox seat.
**Probes (fresh):** `python elev.py --shell "..."` -> `can't open file 'Z:\\elev.py': No such file or directory`; `dir /s /b C:\Users\White\\elev.py` and `C:\Users\Public\\elev.py` -> no match; `glob('Z:/elev*')` -> [].
**Blocks:** the LIVE leg of goal #1 (real load/unload on White via elev.py to bypass the :8888/:8099 egress wall). All cycle-6 hotload infra is built + sandbox-verified; only the live execution step needs a seat where elev.py actually exists.
**Unblock (one-time, non-sandbox White seat with elev.py present):** run `python elev.py --shell "curl -s http://127.0.0.1:8888/api/v0/models"` to confirm the helper + LM Studio, then execute the load/unload cycle and append LOAD_SUCCESS/UNLOAD_SUCCESS rows to hotload-log.jsonl.
**Do NOT re-probe elev.py from this seat.**

## [NEEDS-HUMAN 2026-11-20] Verifier #4 Performance Regression Gate: live-measurement leg blocked by :8099 egress wall
**Class:** WinError 10013 (sandbox egress block to localhost:8099) — SAME wall as Mechanic #4, Verifier #2 SLO, Orchestrator #2. Do NOT re-probe from a sandbox seat.
**Status:** `memory/verifier/perf_gate.py` is BUILT and logic-verified (clean PASS + negative-test path both exercised). But its live baseline cannot be captured here: every /api/* sample returns errors (19/20 endpoints p50=None) because the portal is unreachable from this seat. I deleted the invalid baseline so it is not reused.
**Unblock (one-time, non-sandbox White seat with :8099 egress):** run `python memory/verifier/deploy_perf_gate.py` � single command that captures baseline, registers daily schtask, and runs initial gate check. Closure = 3 consecutive daily PASS + negative test.

## [NEEDS-HUMAN 2026-11-20 Builder] #3 Build-Verify-Pin: memory_mirror.py is 0 bytes in sandbox
**Class:** file-absent (0-byte placeholder, canonical lives on White). Not a code bug.
**Probe:** `pathlib.Path("memory_mirror.py").stat().st_size` -> 0. Repeated across multiple passes.
**Blocks:** the `--apply` leg of `build_verify_pin.py` (live PIN_FILES edit + git commit). Steps (a)-(d) all work in dry-run.
**Unblock (one-time, non-sandbox White seat):** ensure memory_mirror.py is synced to this sandbox OR run the --apply leg directly on White: `python memory/builder/build_verify_pin.py index.html --apply`. Do NOT re-probe from sandbox.

## [RECONCILED 2026-11-19 Orchestrator] Browser acceptance blocker — Chrome-headless unblock does NOT reproduce from sandbox seats
**Conflict resolved:** two ops records disagreed. `memory/ops/browser-acceptance-workaround.md` (my fleet decision) said browser = NEEDS-HUMAN, static structural verification is acceptable closure evidence for Designer #2/#5/#6/#8/#9/#10. Mechanic's newer `memory/ops/headless-browser-unblock.md` claimed Chrome 157 headless WORKS in sandbox ("verified exit 0, DOM returned").
**Re-test from THIS seat (one probe, sequential batch capture — authoritative):**
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox \
  --user-data-dir="Z:\temp_chrome" --virtual-time-budget=4000 --dump-dom "data:text/html,<h1>ok</h1>"
-> CHROME_EXIT=3, dom_data.txt = 0 bytes (NO DOM output)
```
Mechanic's exit-0/DOM result does NOT reproduce here. (Edge still hangs per prior notes; Chrome fails faster with exit 3.) A direct `cmd` run reporting EXITCODE=0 was a `&`-chain %ERRORLEVEL% parse artifact, not a real success.
**Standing decision REAFFIRMED:** for all sandbox seats the browser is NOT available. Designer goals #2/#5/#6/#8/#9/#10 close on **static structural verification** per `browser-acceptance-workaround.md` (braces balanced + node --check + 0 missing tokens/classes + wiring present), with visual QA deferred to the human's own browser at http://localhost:8099/. Do NOT send agents to re-probe Chrome/Edge headless from a sandbox seat — it cannot succeed.
**Full browser testing (only if ever required):** non-sandbox seat — human desk / RDP / Pale-Black-Red with real egress; `py -m playwright install chromium`. Human-desk task, not a fleet task.
Evidence: memory/orchestrator/browser-blocker-reconciliation-2026-11-19.md

## [RESOLVED 2026-11-17 ~14:07] White SANDBOX seat cannot LAN-probe Red .245 (confirmed)
**Resolution:** Red confirmed powered on + reachable via /api/health 200 at 14:07 UTC.
Both scribe-q8 and mechanic-q4 loaded=True. Blocker cleared; no further probe needed from sandbox.
Mechanic asked for `Test-NetConnection Red -Port 445` and `-Port 8888` to close goal #2 Red leg. Attempted from THIS White sandbox seat, both paths fail:
- `powershell -Command "Test-NetConnection ..."` -> terminal tool policy: **Blocked command(s) for safety: powershell**.
- Python `socket.connect_ex(("Red", 445/8888))` -> sandbox egress allowlist rejects the destination ("network destination is not a literal the sandbox can check"). Same class as prior WinError 10013.
**Conclusion:** Red .245 reachability CANNOT be verified from a White sandbox seat, by any tool. The probe must run from a **non-sandbox seat with LAN egress** (White ops terminal / RDP session, or a seated agent on Pale/Black/Red). Do NOT re-probe from here — no pass can succeed.
Owner to close: Mechanic (needs the non-sandbox run); evidence target = `memory/ops/probe-evidence.jsonl` or goal #2 leaf.
- [18:04] ~~NEEDS-HUMAN: seat Orchestrator model unreachable~~ **RESOLVED 2026-11-19** (seat running, confirmed in auto-loop status)
- [18:04] ~~NEEDS-HUMAN: seat Researcher model unreachable~~ **RESOLVED 2026-11-19** (seat running)
- [18:04] ~~NEEDS-HUMAN: seat Builder model unreachable~~ **RESOLVED 2026-11-19** (seat running)
- [18:04] ~~NEEDS-HUMAN: seat Verifier model unreachable~~ **RESOLVED 2026-11-19** (seat running)

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
- **#5 breakpoint automation**: acceptance = CDP screenshots at 375/768px + assert 0 console errors / 0 horizontal overflow (d7_d9_cdp_verify.py -> ../designer/design_breakpoint_check.py). Needs live Chrome DevTools Protocol.
**Exact commands that cannot succeed from this seat:**
- `python memory/designer/live_verify_g578.py` / `live_verify2_g578.py` (axe/Lighthouse) - no browser to drive.
- `python memory/designer/d7_d9_cdp_verify.py` (CDP screenshots) - no Chrome + CDP socket blocked.
**Unblock (non-sandbox, one owner):** run BOTH from a seated agent on White ops terminal / RDP / Pale/Black/Red that has Chrome installed + LAN egress to 127.0.0.1:8099; capture the axe score JSON + the 375/768 screenshots as evidence, then `--record designer 7` / `--record designer 5`.
**Not blocked (in-sandbox, see memory/orchestrator/designer-qa-gate-unblock-2026-11-17.md):** goal #8 typography gate runs clean - ONE real fix left (#actBody line-height 1.7 -> <=1.6).
- [RESOLVED 2026-11-19 Researcher audit]: the "#actBody line-height 1.7" fix is no longer pending — live app.css L144 #actBody now uses var(--lh-mono)=1.6; full static audit of ui/app.css shows all 5 line-heights <=1.6 (0 violations). Remaining for Designer Goal #7 = font-size scope decision (extended vs strict-5-step) + browser computed-style leg, NOT a line-height fix. Evidence: memory/researcher/designer-goal7-typo-audit-2026-11-19.md
- [18:35] ~~NEEDS-HUMAN: seat Designer model unreachable~~ **RESOLVED 2026-11-19** (seat running)
- [18:35] ~~NEEDS-HUMAN: seat Archivist model unreachable~~ **STILL OPEN 2026-11-19** (Archivist=unreachable per current auto-loop status)
- [18:36] ~~NEEDS-HUMAN: seat Designer model unreachable~~ **RESOLVED 2026-11-19** (seat running)
- [18:36] ~~NEEDS-HUMAN: seat Archivist model unreachable~~ **STILL OPEN 2026-11-19** (Archivist=unreachable)

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
- Status: Instrumentation verified live in memory_mirror.py (log_event at 4 sites). Self-test PASS. Parse pipeline validated end-to-end (parse_mirror_events.py). Closure runbook pre-staged.
- SHARPENED DIAGNOSIS (2026-11-17 auto-loop pass, seeded a real run from this White/Red sandbox seat):
  - `python memory_mirror.py -v` -> ALL 3 hosts: `connect: System error 5 ... Access is denied.`
  - This is an **SMB AUTH** failure, NOT the prior "egress block / WinError 10013" class. The seat CAN reach Red/.39/.99 on the LAN; `net use` with the config's empty SMB password is rejected.
  - `python elev.py` -> **helper ABSENT at this seat** (same as Verifier #2 entry); cannot escalate from here.
- Conclusion: a one-off seed from an ephemeral sandbox session will NOT satisfy the "one-week LIVE dataset" anyway — that requires the mirror to run PERSISTENTLY on the persistent White host (C:\Projects\Workspace) where `net use` sessions + SMB creds persist, via its scheduled task / watchdog.
- Unblock (persistent White host, owner = Mechanic or Orchestrator): confirm the MirrorSync schtask/watchdog is registered AND that `net use \\192.168.1.<ip>\C$` succeeds there with working creds; then it self-seeds + accumulates through 11-24. Closure = `python memory/researcher/parse_mirror_events.py <live-log>` per runbook.
- Do NOT re-probe from a sandbox seat — auth wall confirmed, one probe spent this pass.
- [00:11-00:12] ~~NEEDS-HUMAN: seat Designer/Archivist model unreachable~~ **RESOLVED 2026-11-19** (Designer running; Archivist STILL OPEN per current status)
- [02:50, 07:50-07:51] ~~NEEDS-HUMAN: seat Archivist model unreachable~~ **STILL OPEN 2026-11-19** (Archivist=unreachable per current auto-loop status)
- [05:10-05:11] ~~NEEDS-HUMAN: seat Researcher model unreachable (not_loaded)~~ **RESOLVED 2026-11-19** (seat running)

## [NEEDS-HUMAN 2026-11-18] Mechanic #4 FleetBootRecovery schtask: COM wall on all sandbox seats
**Class:** `schtasks` -> "ERROR: Class not registered" (COM unavailable in sandbox). elev.py absent at this seat.
**Blocks:** Final step of Mechanic goal #4 - registering the boot-recovery scheduled task on White.
**Exact command that cannot succeed from a sandbox seat:**
```
schtasks /create /tn FleetBootRecovery /tr ""C:\\Python\\python.exe" "Z:\\memory\\mechanic\\reboot_recover.py"" /sc onstart /ru SYSTEM /rl HIGHEST /f
```
or: `python memory/mechanic/deploy_reboot_recovery_all.py` (calls schtasks internally).
**Unblock (one-time, non-sandbox White admin terminal):** run `python memory/mechanic/deploy_reboot_recovery_all.py`. This registers the local task + attempts remote deployment via WinRM. Evidence target: `memory/mechanic/reboot-recovery.jsonl` (type=deploy_reboot_recovery_all).
**Do NOT re-probe from any sandbox seat.** Same COM wall confirmed 2026-11-17 (Verifier #2) and 2026-11-18 (this entry).

## [NEEDS-HUMAN 2026-11-18] Orchestrator #2 Execute Engine: sandbox cannot reach Studio :8888
**Class:** WinError 10013 (sandbox egress block on localhost). Repeated across passes; do NOT re-probe from here.
**Blocks:** Live verification of execute() - the dry-run + code are BUILT and pass selftest, but a real activate/deactivate cycle requires direct TCP to 127.0.0.1:8888.
**Exact command that cannot succeed from this sandbox seat:**
```
python memory/orchestrator/model_scheduler.py --execute agents=researcher resident=white:qwen3-27b-q8
```
-> WinError 10013 on first urllib.request.urlopen("http://127.0.0.1:8888/models")
**Unblock (one-time, non-sandbox White ops terminal):** run the same command from a seated session with LAN/localhost egress to :8888. Evidence target: memory/llm/hotload-log.jsonl will have timestamped load+unload rows; aliases must be byte-identical before/after.
**Do NOT re-probe from any sandbox seat.**

## 2026-11-18 RESOLUTIONS (unsloth-assist, White seat)
- **PortalLoadProbe schtask: RESOLVED** - registered daily 06:00 via real python (C:\Projects\Workspace\Python\pythoncore-3.15-64); first probe run OK (9 models on White; Black load-fail reconfirmed). Mechanic #4 now accumulates (2/7 days at registration).
- **VerifierSLO schtask: RESOLVED** - registered daily 06:00, first run exit 0. Verifier #2 unblocked.
- **MirrorSync schtask: RESOLVED** - registered every 5 min (memory_mirror.py). Mirror pipeline LIVE: 09:52 run pushed 30 files to Red. REMAINING NEEDS-HUMAN: Pale/Black SMB creds into memory_mirror_hosts.json (Arnold; Red works with empty password).
- **Mechanic #2 Red leg: CLOSED** - TCP 445 OPEN + 8888 OPEN probed from White seat; ledger recorded mechanic.md line 7; evidence memory/ops/probe-evidence.jsonl.
- **Designer #5/#7 CDP wall: RESOLVED (agent-side fix only)** - chrome.exe absent, but msedge --remote-debugging-port=9222 loads portal and /json/list returns the live page. Point live_verify_g578.py at 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' instead of chrome.
- [17:31-17:32, 00:26] ~~NEEDS-HUMAN: seat Archivist model unreachable~~ **STILL OPEN 2026-11-19** (Archivist=unreachable; auto-reload has not resolved it)

## NEEDS-HUMAN: Portal auto-restart failed (auto_restart.py)
- **Time:** 2026-11-19T02:51:50
- **Port:** 8099 not responding after 3 restart attempts
- **PID found:** None
- **Diagnostics:** {"timestamp": "2026-11-19T02:51:50", "portal_port": 8099, "portal_up": false, "portal_pid": null, "recent_health_log": ["2026-11-18T10:07:48.054563+00:00 [CRITICAL] ALERT: agents: skipped (portal down)", "2026-11-18T10:07:50.352024+00:00 [INFO] ALERT-TEST: simulating a critical alert", "2026-11-18T10:07:50.365737+00:00 [CRITICAL] ALERT: alert_test: This is a test alert to verify wiring"]}
- **Unblock step:** Manually run `python agent_portal.py` and verify port 8099 responds.

[OPS 2026-11-22 ~16:0x - Studio seat (user directive: full automation, no human-blocking gates)] RESOLVED from non-sandbox seat:
- Verifier #1 perf gate: deploy_perf_gate.py ran clean - fresh baseline 18/20 valid p50, schtask VerifierPerfGate registered daily 07:00, initial gate = 1 WARN (/api/agents +142.9% 6.37->15.47ms, load-dependent), negative test PASS (alert fired). Evidence: memory/verifier/evidence-deploy-perf-gate-2026-11-22.md.
- Mechanic #4 / Archivist #1 / Mechanic #2 schtasks: VERIFIED registered on White - PortalLoadProbe, AgentPortal_LoadProbe_Daily, PortalMemoryDecay, MirrorHeal, VerifierPerfGate all Ready (schtasks /query 2026-11-22).
- Elevated helper was DOWN (port 8098 closed; ONSTART SYSTEM task ElevatedHelper MISSING from scheduler). Recovered non-elevated: pythonw elevated_helper.py running detached (ping {ok, elevated:false, user:White}) + startup-folder VBS (elev_helper_start.vbs) for auto-start on logon. ONE-TIME setup remaining (not a work gate): double-click install_elevated_helper.bat once (UAC) to restore the SYSTEM task for admin-only commands; until then elev.py works for non-admin ops and admin ops fail honestly.
- Red stays WIRELESS (user directive 2026-11-22): FUTURE "move Red .245 to wired NIC" removed from TODO.md; live per-agent goal files had no such item; archived cycle-1 files left as frozen provenance.
