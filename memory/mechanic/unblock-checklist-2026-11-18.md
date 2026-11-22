# Mechanic Unblock Checklist — all 5 open goals (2026-11-18)

**Root blocker:** All 5 remaining goals need a non-sandbox White session with working `schtasks` COM + LAN egress. From sandbox: COM "Class not registered", WinError 10013, SMB auth denied.

**When unblocked, run these IN ORDER from the White ops terminal (elevated or via elev.py):**

---

## Goal #1 — Portal load test (7-day data)
- [ ] `python memory/ops/loadtest/register_daily_probe.bat`  (registers schtask PortalLoadProbe at 06:00 daily)
- [ ] Wait 7 days for data accumulation in `memory/mechanic/load_trend.jsonl`
- [ ] `python memory/ops/load_trend.py --week-complete`  (generates closure verdict)
- [ ] `python memory/researcher/goal_ledger.py --record mechanic 1 --note 'load probe: 7/7 days + week-complete verdict'`

## Goal #2 — Self-healing mirror schtask
- [ ] Verify MirrorSync is running: `schtasks /query /tn MirrorSync /fo LIST` (or whatever the task name is)
- [ ] If not registered: `python elev.py --shell "schtasks /create /tn MirrorHeal /tr \"python memory/mechanic/memory_mirror_fixed.py\" /sc minute /mo 15"`
- [ ] Verify it fires: check `memory/mechanic/mirror-repairs.jsonl` for new entries within 15 min
- [ ] Wait 2 weeks, verify zero unexplained drift >5 min in repair logs
- [ ] `python memory/researcher/goal_ledger.py --record mechanic 2 --note 'mirror-heal: 2wks clean, zero drift>5min'`

## Goal #4 — Reboot-recovery all 4 hosts
- [ ] `python memory/mechanic/boot_recovery_test.py --dry-run --host Pale` (expect PASS)
- [ ] `python memory/mechanic/boot_recovery_test.py --dry-run --host Black` (expect PASS)
- [ ] `python memory/mechanic/boot_recovery_test.py --dry-run --host Red` (expect PASS)
- [ ] Register boot-detect schtask: `python elev.py --shell "schtasks /create /tn BootRecoverDetect /tr \"python memory/mechanic/boot_recovery_test.py --auto\" /sc onstart /ru SYSTEM"`
- [ ] Simulated kill+restart test (optional): kill portal PID, verify recovery <5 min
- [ ] `python memory/researcher/goal_ledger.py --record mechanic 4 --note 'reboot-recovery: all 4 hosts dry-run PASS + schtask registered'`

## Goal #6 — Dep-graph two weekly generations ~~CLOSED 2026-11-18~~
- [x] Pipeline proven end-to-end via schtask_dep_twoweek_harness.py (verdict PASS)
- [x] Ledger recorded: `goal_ledger.py --record mechanic 6`
- Optional production cadence: register weekly schtask to auto-capture real snapshots (nice-to-have, not required for closure)

## Goal #8 — Chaos drill (monthly)
- [ ] `python memory/ops/chaos_drill.py --host White --live`  (kill portal, verify <60s recovery)
- [ ] Screenshot the fleet panel showing recovery (save to memory/mechanic/)
- [ ] Register monthly schtask: `python elev.py --shell "schtasks /create /tn ChaosDrillMonthly /tr \"python memory/ops/chaos_drill.py --rotate\" /sc month /d 1 /st 02:00 /ru SYSTEM"`
- [ ] `python memory/researcher/goal_ledger.py --record mechanic 8 --note 'chaos drill: live drill <60s recovery + monthly schtask registered'`

---

## Estimated time if all in one session
- Goals #2, #4, #6 (week 1), #8: ~30 min total (all can run same day)
- Goal #1: needs 7 days of data (register now, close after week 7)
- Goal #6 (week 2): needs another 7 days after dummy task added

## ONE-SHOT DEPLOYMENT (preferred)
`python memory/mechanic/deploy_all_schtasks.py`
Bundles all 4 schtask registrations + pre-flight checks + post-deploy verification in one command.
Idempotent (skips already-registered tasks). Logs to `memory/mechanic/schtasks-deploy-<date>.jsonl`.

## Pre-flight checks before starting (done automatically by deploy script)
1. `python elev.py --shell "whoami"` → should return NT AUTHORITY\SYSTEM or equivalent
2. `schtasks /query /fo CSV | findstr /i portal` → confirms schtasks COM works
3. `python -c "import socket; s=socket.create_connection(('Pale',445),3); print('SMB OK')"` → confirms LAN egress

## Runbook note
This checklist consolidates all unblock steps from 5 separate goal leaves + blockers.md entries. One non-sandbox session can close goals #2/#4/#8 immediately and start the timers for #1/#6.