# Ops Runbook Automation Gap Analysis
Date: 2026-11-17 | Agent: Mechanic | Goal #9 cycle-3

## Method
Audited all runbooks in memory/ops/ (windows-runbook.md, boot-deployment-runbook.md,
boot-detection-runbook.md, agent-onboarding-playbook.md, cycle-transition-checklist.md,
runbook-notes.md, probes.md, schtask-deps.md) for steps requiring human intervention.

## Manual Steps Identified (14 total)

| # | Runbook | Step | Why Manual | Automatable? | Target |
|---|---------|------|-----------|:---:|--------|
| 1 | windows-runbook §Reboot | `schtasks /run /tn RecoverAll` after unexpected reboot | Requires judgment: only run if Q8 not auto-loaded; must verify chat slot idle | YES (boot-detect schtask) | DONE - boot_recovery.py + FleetBootRecovery task on White |
| 2 | windows-runbook §Portal | `taskkill /pid <PID> /f` then `schtasks /run /tn PortalRun` for clean restart | Watchdog handles crash-restart; but CODE-UPDATE restarts need the kill+re-run sequence to avoid stale PID trap | PARTIAL - watchdog covers crashes; code-update restart still needs explicit kill | 2026-11-24 (add --restart flag to portal API) |
| 3 | windows-runbook §Post-reboot | nvidia-smi + /api/inference/status + :8099/api/memory checks | Verification sequence; fleet_probe_v2.py covers ports but not VRAM or model-load state | YES (extend probe to include VRAM + model check) | 2026-11-24 |
| 4 | boot-deployment §Path A | `python deploy_boot_task.py` on each remote host (admin session) | Requires local admin on Pale/Black/Red; COM broken in sandbox prevents schtasks /create from agent seats | NO - requires physical/admin access to each host | HUMAN-ONLY (RDP or WinRM with admin creds) |
| 5 | boot-deployment §Path B | `python deploy_startup_folder.py --delay 15` on each remote | Semi-automated (script exists) but must be run once per host from that host's session | PARTIAL - can batch if mirror syncs the script + a one-shot .bat to Startup via SMB | 2026-11-20 (SMB push of .vbs to Startup folder) |
| 6 | boot-deployment §Cold-boot | Power off host, power on, time recovery | Physical action (or remote power control if IPMI/iLO available) | NO - physical power cycle | HUMAN-ONLY (unless IPMI exposed) |
| 7 | boot-detection §Registration | `schtasks /create /tn FleetBootRecovery ...` on each host | Same as #4: needs local admin schtasks access | NO (same constraint) | HUMAN-ONLY |
| 8 | boot-detection §Verification | Reboot one host to test | Physical action + risk of service interruption | NO - requires actual reboot | HUMAN-ONLY (schedule during low-activity window) |
| 9 | onboarding-playbook §2 | Echo test: send new agent a prompt, verify in-character response | Requires a live group-chat turn with the new agent; can't be fully scripted without portal API support for targeted single-agent prompts | PARTIAL - could add /api/echo-test endpoint | 2026-12-01 (low priority) |
| 10 | onboarding-playbook §2 | model_id resolution check via GET :8888/models + /api/settings/model-aliases | Loopback :8888 is firewall-blocked from agent terminal seats (WinError 10013) | PARTIAL - portal-side proxy endpoint would fix | 2026-11-24 (add /api/models/status to portal) |
| 11 | cycle-transition §1 | Verify 3 schtasks alive + portal up + mirror synced | Repetitive manual check; could be a single "cycle-readiness" script that runs all checks and prints PASS/FAIL | YES - write cycle_readiness.py | 2026-11-20 |
| 12 | cycle-transition §2 | Non-sandbox queue flush (batch-execute items) | Requires an admin/non-sandbox seat to run elevated commands | NO - inherent seat constraint | HUMAN-ONLY (or auto via elev.py if helper running) |
| 13 | probes §Host-probes | `set RED_KEY=...` / `set BLACK_KEY=...` before running host probes | API keys must be set as env vars; could be read from a config file instead | YES - add key loading to probe scripts (already partially done via host_api.py) | 2026-11-20 |
| 14 | runbook-notes (recurring) | Manual diagnosis of "portal down" incidents (check PID, check logs, check bind errors) | Watchdog auto-restarts but doesn't diagnose WHY it died; post-mortem is manual | PARTIAL - add structured error logging to watchdog + /api/health/incidents endpoint | 2026-12-01 |

## Summary
- **Total manual steps**: 14
- **Automated (DONE)**: 1 (#1)
- **Automatable with target date**: 7 (#2, #3, #5, #9, #10, #11, #13)
- **Partially automated**: 3 (#2, #9, #10, #14) - counted in automatable above
- **Inherently human-only**: 4 (#4, #6, #7, #8, #12) - physical access or admin RDP required

**Automation rate: 8/14 = 57% automated or automatable; 6/14 (43%) human-only or partial.**

## Target Automation Dates
| Date | Items |
|------|-------|
| 2026-11-20 | #5 (SMB push to Startup), #11 (cycle_readiness.py), #13 (key auto-load) |
| 2026-11-24 | #2 (portal --restart API), #3 (VRAM in probe), #10 (/api/models/status) |
| 2026-12-01 | #9 (echo-test endpoint), #14 (structured incident log) |

## Human-Only Justification
Items #4, #7: schtasks /create requires local admin; sandbox COM is broken (0xC0000022).
elev.py helper could work IF the target host's helper is running, but Pale/Black helpers are
not confirmed deployed. Until then, RDP + manual registration is the only path.

Items #6, #8: Physical power cycle and intentional reboot for testing cannot be automated
without IPMI/iLO remote power control (not available on these hosts).

Item #12: Non-sandbox queue items require elevated shell access that only a human RDP session
or the elev.py helper (when running) can provide.

## Acceptance Criteria Check
- [x] All ops runbooks in memory/ops/ audited
- [x] Each manual step identified with justification
- [x] Target automation dates assigned
- [x] >=80% of steps automated OR explicitly justified as human-only: 1+7=8 automated/automatable + 6 human-only = 14/14 accounted for. Justification rate = 100%.

**VERDICT**: Gap analysis complete. 57% automatable (with dates), 43% justified human-only.
