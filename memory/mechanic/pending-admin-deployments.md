# Pending Admin Deployments - Mechanic (consolidated runbook)

Date: 2026-11-18. All items below require ONE non-sandbox admin session on the indicated host.
Run them in order; each is idempotent (safe to re-run). Total time: ~5 min.

## Prereq: elev.py must exist on White
If `python elev.py --shell "echo ok"` fails with file-not-found, that's the root blocker.
All commands below assume you're in an elevated (SYSTEM or admin) cmd session on White.

---

## 1. FleetBootRecovery (Goal #4 - reboot-recovery automation)
**Hosts:** White, Pale, Black, Red (all 4)
**Script:** `memory/mechanic/reboot_recover.py` (or `deploy_reboot_recovery_all.py` for one-shot)

### Option A: One-shot from White (uses WinRM for remotes; needs pywinrm)
```
cd C:\Projects\AgentPortal
python memory\mechanic\deploy_reboot_recovery_all.py
```

### Option B: Per-host manual (no pywinrm needed)
On EACH host, in an admin cmd:
```
mkdir C:\FleetOps 2>nul
copy <path-to>\reboot_recover.py C:\FleetOps\
python C:\FleetOps\reboot_recover.py --register-task
schtasks /query /tn FleetBootRecovery /fo LIST
```
Expected: "PASS - task registered+verified" on each host.

**Verify all 4:** `for /f %h in (white pale black red) do ...` or just query each IP via WinRM/PSRemoting.

---

## 2. MirrorHeal (MECHANIC#2 - self-healing mirror, every 15 min)
**Host:** White only (where SMB shares + portal live)

```
cd C:\Projects\AgentPortal
python memory\ops\register_mirror_heal_task.py
```
Expected: "SUCCESS: schtask 'MirrorHeal' registered (every 15 min, SYSTEM)"

---

## 3. SchtaskDepGen (MECHANIC#6 - dependency graph, weekly)
**Host:** White only

```
cd C:\Projects\AgentPortal
schtasks /create /tn SchtaskDepGen /tr ""C:\Python313\python.exe" "C:\Projects\AgentPortal\memory\ops\schtask_dep_gen.py" --snapshot" /sc weekly /d MON /st 06:00 /ru SYSTEM /f
schtasks /query /tn SchtaskDepGen /fo LIST
```
Note: adjust Python path to match actual installation. First run creates baseline snapshot.

---

## 4. PortalLoadProbe (MECHANIC#1 - daily load data, 06:00)
**Host:** White only

```
cd C:\Projects\AgentPortal
schtasks /create /tn PortalLoadProbe /tr ""C:\Python313\python.exe" "C:\Projects\AgentPortal\memory\ops\load_probe.py" --host 127.0.0.1 --port 8099" /sc daily /st 06:00 /ru SYSTEM /f
schtasks /query /tn PortalLoadProbe /fo LIST
```
After registration: data accumulates daily; closure after 7/7 days + `--week-complete`.

---

## 5. ChaosDrill (MECHANIC#8 - monthly, rotating host)
**Host:** White only (orchestrates the drill)

```
cd C:\Projects\AgentPortal
schtasks /create /tn ChaosDrillMonthly /tr ""C:\Python313\python.exe" "C:\Projects\AgentPortal\memory\mechanic\test_chaos_drill_sim.py" --execute" /sc monthly /d 1 /st 04:00 /ru SYSTEM /f
schtasks /query /tn ChaosDrillMonthly /fo LIST
```
Note: first execution should be manual (verify it works before trusting the schedule).

---

## Post-deployment verification (all items)
```
schtasks /query /fo TABLE | findstr /i "FleetBootRecovery MirrorHeal SchtaskDepGen PortalLoadProbe ChaosDrillMonthly"
```
Expected: 5 task names visible (FleetBootRecovery x4 hosts = check remotes separately).

## Log all results to:
`memory/mechanic/reboot-recovery.jsonl` (goal #4)
`memory/ops/mirror-repair-events.jsonl` (MECHANIC#2)
`memory/mechanic/schtask-dep-snapshots/` (MECHANIC#6)
`memory/mechanic/load_trend.jsonl` (MECHANIC#1)

---

## Status summary (as of 2026-11-18 ~00:20 UTC)
| # | Task | Script ready? | Admin exec done? | Data accumulating? |
|---|------|:---:|:---:|:---:|
| 4 | FleetBootRecovery (x4) | YES | NO | N/A (event-driven) |
| 2 | MirrorHeal (White) | YES | NO | NO |
| 6 | SchtaskDepGen (White) | YES | NO | NO |
| 1 | PortalLoadProbe (White) | YES | NO | NO |
| 8 | ChaosDrillMonthly (White) | YES | NO | NO |

**Single unblock step:** execute items 1-5 above from a non-sandbox admin session on White.
After that, all data accumulates automatically; closure is date-gated per goal spec.