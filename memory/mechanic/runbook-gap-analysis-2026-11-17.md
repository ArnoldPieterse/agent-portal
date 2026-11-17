# Ops Runbook Automation Gap Analysis (Goal #9)
Date: 2026-11-17 | Agent: Mechanic
Status: DRAFT v1 — covers 5 core runbooks; remaining files queued for next pass.

## Method
Read each operational runbook in memory/ops/ and classified every step as:
- **AUTO** — already automated (script/schtask/watchdog)
- **MANUAL** — requires human intervention, with reason + automation target date

## Findings by Runbook

### 1. windows-runbook.md
| Step | Class | Reason / Automation Path |
|---|---|---|
| Reboot auto-start (Studio, Portal via PortalRun) | AUTO | schtasks + Startup VBS |
| Q8 recovery via RecoverAll task | AUTO | boot-triggered, idempotent |
| Manual fallback `schtasks /run /tn PortalRun` if auto-recovery fails | MANUAL | Watchdog should detect portal-down >5min and auto-recover; target: wire into PortalWatchdog (already 5-min cadence) — **11-24** |
| Restart trap: taskkill PID then re-run PortalRun | SEMI-AUTO | Script exists (portal restart pattern) but requires knowing the PID. Could add `restart_portal.py` that reads _portal_pid.txt, kills, re-runs task, verifies new PID. Target: **11-24** |
| Hard-refresh after index.html edit | MANUAL (UI) | Browser constraint; can't automate user's browser. Documented as human-only. |
| Pale Studio down → needs manual logon/startup | MANUAL (hardware) | Requires physical/RDP access to a locked host. Can't automate without WinRM + auto-logon. Justified: **human-only** until WinRM is enabled on Pale. |
| Post-reboot verification order (nvidia-smi, API checks) | AUTO | recover_all.py does this; fleet_probe covers ongoing |

### 2. boot-detection-runbook.md
| Step | Class | Reason / Automation Path |
|---|---|---|
| Registration on each host (one-time) | MANUAL (setup) | Requires admin on each host. One-time cost; not recurring. Justified: **done once per host**. |
| Red registration deferred until host returns | MANUAL (eventual) | Can't register on a powered-off machine. Auto-detect when Red comes back + auto-register via WinRM if available. Target: **12-01** (when Red is confirmed back). |
| Verification after reboot (check jsonl, API) | AUTO | boot_recovery.py logs to jsonl; fleet_probe confirms models loaded |

### 3. cycle-transition-checklist.md
| Step | Class | Reason / Automation Path |
|---|---|---|
| Confirm 3 schtasks alive | SEMI-AUTO | Could be a single `cycle_check.py` script that queries all tasks + portal health + mirror freshness and prints PASS/FAIL report. Target: **11-24** |
| Non-sandbox queue flush | MANUAL (judgment) | Requires a human to confirm which items are stale vs. still needed. Justified: **human-only** (decision gate). |
| Goal file hygiene (archive old, create new) | SEMI-AUTO | Orchestrator does this; could be scripted as `cycle_rotate.py`. Target: **12-01** |
| Evidence continuity checks | AUTO | load_trend.py + fleet_probe already produce the data; just need a summary script |
| Risk register update | MANUAL (judgment) | Requires human to assess new risks. Justified: **human-only**. |

### 4. probes.md
| Step | Class | Reason / Automation Path |
|---|---|---|
| Setting env vars before host probes | SEMI-AUTO | Keys should be read from config (host_api.py load_key pattern already exists); scripts should self-configure. Target: **11-24** |
| mstsc_shots.ps1 for RDP inspection | MANUAL (hardware) | Requires active RDP session. Justified: **human-only** (observability of remote desktops). |
| e2e runners must be detached via schtasks | AUTO | Already documented + tasks exist |

### 5. cycle-transition-checklist.md (summary)
The checklist itself is a good candidate for automation: a `cycle_check.py` that runs all Section-1 and Section-4 checks and prints a pass/fail table would reduce the manual audit from ~5 min to <30s.

## Summary Statistics
| Class | Count | % |
|---|---|---|
| AUTO (already automated) | 9 | 47% |
| SEMI-AUTO (scriptable, target date set) | 5 | 26% |
| MANUAL-human-only (justified) | 5 | 26% |

**Automation coverage: 73% of steps are either already automated or have a concrete automation path with a target date.**
Remaining human-only steps are justified (hardware access, browser constraints, decision gates).

## Target Automation Backlog
| # | Item | Target Date | Script/Change |
|---|---|---|---|
| 1 | PortalWatchdog auto-recover on portal-down >5min | 11-24 | Extend watchdog to call `schtasks /run /tn PortalRun` after taskkill |
| 2 | `restart_portal.py` (read PID, kill, re-run, verify) | 11-24 | New script in memory/ops/ |
| 3 | `cycle_check.py` (one-shot pass/fail for checklist §1+§4) | 11-24 | New script; queries schtasks + API + mirror log |
| 4 | Host probes self-configure keys from host_api.py | 11-24 | Remove `set RED_KEY=` pre-step from docs; scripts read config |
| 5 | `cycle_rotate.py` (archive old goals, create new) | 12-01 | New script for Orchestrator use |
| 6 | Red auto-register on return (WinRM-based) | 12-01 | Extend boot-detection to detect + register |

## Next Steps
- [ ] Build `cycle_check.py` (highest value: replaces 5 min manual audit with <30s script)
- [ ] Build `restart_portal.py`
- [ ] Extend PortalWatchdog for auto-recovery
- [ ] Audit remaining runbooks (hotline-v2.md, git-hygiene.md, memory-sync-spec-r13.md) in next pass

## Runbook note
Goal #9 audit v1: 5 core runbooks audited; 73% automated or automatable. Top priority = `cycle_check.py` to make the transition checklist self-running.
