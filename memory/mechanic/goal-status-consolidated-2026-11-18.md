# Mechanic Open-Goals Status (auto-loop pass 2026-11-18)

## Summary: 5 open goals, all blocked on sandbox limitations (no network, no schtasks)

| # | Goal | Blocker Class | Unblock (one-time, non-sandbox) |
|---|------|--------------|-------------------------------|
| 1 | Portal load test (7-day data) | Egress block: cannot reach 127.0.0.1:8099 | Register schtask on White: `python elev.py --shell "schtasks /create /tn FleetLoadProbe /tr \"python C:\\Projects\\Workspace\\memory\\mechanic\\fleet_load_probe.py\" /sc minute /mo 30"` |
| 2 | Self-healing mirror (15-min task) | SMB Access Denied + no schtasks COM | Confirm MirrorSync schtask on persistent White host; verify `net use \\192.168.1.x\C$` works there |
| 4 | Reboot-recovery all 4 hosts | Egress block: cannot TCP-check remote hosts | Run `python memory/mechanic/reboot_recovery_test.py --dry-run` from non-sandbox seat with LAN egress |
| 6 | Schtask dep graph (weekly) | No schtasks COM in sandbox | Run `python memory/ops/schtask_dep_gen.py --capture` from non-sandbox seat; register weekly task |
| 8 | Chaos drill (monthly) | Cannot kill/reach portal | Execute from non-sandbox seat: kill portal PID, time recovery via probe |

## What I CAN do from this sandbox (done this pass)
- Verified all scripts exist and are syntactically valid
- Confirmed blockers are identical across goals (sandbox egress + COM class)
- This status file serves as the single reference for unblock sequencing

## Recommended unblock order (one human/ops session on White)
1. Register FleetLoadProbe schtask (goal #1) - starts 7-day clock immediately
2. Confirm MirrorSync is running (goal #2) - check `schtasks /query /tn MirrorHeal`
3. Run reboot_recovery_test.py --dry-run (goal #4) - single command, instant result
4. Run schtask_dep_gen.py --capture (goal #6) - single command
5. Chaos drill (goal #8) - schedule for end of session

## Evidence
- load_trend.jsonl: 1 entry (ERR:URLError, 2026-11-18T04:18)
- mirror-repairs.jsonl: 2 entries (dry_run + repair_partial with SMB auth fail)
- reboot-recovery.jsonl: existing entries from prior passes
- All scripts present and <5KB each
