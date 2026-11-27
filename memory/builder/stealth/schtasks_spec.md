# Stealth Workflow — Fleet Deployment via schtasks
Owner: Builder (wrapper) + Mechanic (deployment)
Date: 2026-11-25
Status: READY FOR MECHANIC TO DEPLOY

## Prerequisites
- `run_stealth_jobs.py` in `memory/builder/stealth/` (selftest 5/5 PASS)
- Input files per client in `<client_dir>/input/`:
  - `invoices.json` (for wf1)
  - `metrics.jsonl` (for wf2)
  - `schedule.json` (for wf3)
- Python 3.9+ on target host

## Resource Budget (baked into wrapper)
| Constraint | Value | Protection |
|-----------|-------|------------|
| Max RSS | 256 MB | Linux: RLIMIT_AS; Windows: wall-clock timeout as backstop |
| Max wall-clock | 120 s/job | Prevents starvation of model seats |
| Network | None | Offline-only, no API calls |
| Execution | Sequential | 'all' mode runs wf1→wf2→wf3 in order |

## schtasks Commands (per client host)
> Replace `C:\clients\<CLIENT>` with the actual client data directory.
> Run as SYSTEM or a dedicated service account.

### Daily at 07:00 — AR Follow-ups (wf1)
```bat
schtasks /create /tn "Stealth_WF1_AR_Followup_<CLIENT>" /tr "python C:\Projects\AgentPortal\memory\builder\stealth\run_stealth_jobs.py wf1 --input-dir C:\clients\<CLIENT>\input --output-dir C:\clients\<CLIENT>\output" /sc daily /st 07:00 /ru SYSTEM /rl LIMITED /f
```

### Weekly Monday 06:00 — KPI Report (wf2)
```bat
schtasks /create /tn "Stealth_WF2_Weekly_Report_<CLIENT>" /tr "python C:\Projects\AgentPortal\memory\builder\stealth\run_stealth_jobs.py wf2 --input-dir C:\clients\<CLIENT>\input --output-dir C:\clients\<CLIENT>\output" /sc weekly /d MON /st 06:00 /ru SYSTEM /rl LIMITED /f
```

### Daily at 08:00 — Reminder Pipeline (wf3)
```bat
schtasks /create /tn "Stealth_WF3_Reminders_<CLIENT>" /tr "python C:\Projects\AgentPortal\memory\builder\stealth\run_stealth_jobs.py wf3 --input-dir C:\clients\<CLIENT>\input --output-dir C:\clients\<CLIENT>\output" /sc daily /st 08:00 /ru SYSTEM /rl LIMITED /f
```

## Staggering (avoid thundering herd on shared hosts)
If multiple clients share a host, offset start times by 15 min per client:
- Client A: 07:00 / 06:00 / 08:00
- Client B: 07:15 / 06:15 / 08:15
- Client C: 07:30 / 06:30 / 08:30

## Monitoring
- Log file: `memory/builder/stealth/stealth-jobs.log.jsonl`
- Each entry: `{ts, job, status, elapsed_s, detail}`
- Status values: PASS, FAIL, BUDGET_EXCEEDED, INPUT_MISSING
- Exit codes: 0=OK, 1=logic fail, 2=budget exceeded, 3=input missing

## Rollback
```bat
schtasks /delete /tn "Stealth_WF1_AR_Followup_<CLIENT>" /f
schtasks /delete /tn "Stealth_WF2_Weekly_Report_<CLIENT>" /f
schtasks /delete /tn "Stealth_WF3_Reminders_<CLIENT>" /f
```

## Verification (Mechic to run post-deploy)
1. `schtasks /query /tn "Stealth_WF1_AR_Followup_TEST" /v /fo list` → shows Next Run Time
2. Manual trigger: `schtasks /run /tn "Stealth_WF1_AR_Followup_TEST"`
3. Check log: `type memory\builder\stealth\stealth-jobs.log.jsonl | findstr PASS`
4. Verify no model seat impact: check VRAM before/after (should be <5 MB delta)
