# Goal 3: WinRM Remote Reboot E2E Test — Progress (2026-11-20)

## Status: TIER-A COMPLETE. Live execution queued for non-sandbox seat.

### What's verified so far
| Component | Status | Evidence |
|---|---|---|
| Remote watchdog deployed (FleetBootRecovery) | PASS on PALE+BLACK+RED | `reboot-recovery.jsonl` 2026-11-20T03:44, all 3 hosts ok=true, verified=true |
| Watchdog logic (port 8888 check + studio relaunch) | PASS | `deploy_watchdog_remote.py` PS1 script; 5-min repetition interval |
| WinRM connectivity to PALE+BLACK | PASS | TCP 5985 OK, HTTP 401 Negotiate challenge (goal1-winrm-sandbox-probe) |
| E2E test harness built | PASS | `e2e_anti_stall_test.py` (201 lines), py_compile clean |

### What remains (single action from non-sandbox White)
```
cd Z:\memory\mechanic
python e2e_anti_stall_test.py --host BLACK
```
Expected: ~5-10 min cycle (watchdog interval is 5 min). Output: PASS/FAIL verdict + timeline in `reboot-recovery.jsonl`.

### Acceptance criteria mapping
| Criterion | How the script verifies it |
|---|---|
| Full cycle <15 min | `total_cycle_s` tracked, verdict FAIL if >900s |
| All log entries in correct order | JSONL timeline: 1_verify_up → 2_stop_studio → 3_recover → 4_agent_response → VERDICT |
| Agent responsive after recovery | Step 4: HTTP GET /api/health on target |
| No data loss | (implicit: studio relaunch preserves state; verify via agent response) |

### Blocker (environmental, already recorded)
Sandbox has WinError 10013 (egress blocked) + SSPI wall (no LSA token). Both documented in `memory/ops/blockers.md`. The test requires a non-sandbox seat with network egress to 192.168.1.x and NTLM auth capability.

### Runbook note
If E2E fails at step 3 (no recovery within 15 min): check `C:/FleetOps/watchdog.log` on target host via WinRM; if watchdog didn't fire, the schtask may have been disabled — re-run `deploy_watchdog_remote.py`.
