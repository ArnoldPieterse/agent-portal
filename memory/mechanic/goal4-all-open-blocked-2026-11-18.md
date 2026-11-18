# Mechanic Goal Status - 2026-11-18 (Red sandbox seat)

## All 4 open goals blocked by same class: sandbox COM + egress

| Goal | Blocker | Unblock (single step from White admin) |
|------|---------|---------------------------------------|
| #1 Portal load test | Data accumulates on White via schtask; can't read/verify from Red | `python memory/ops/load_trend.py --week-complete` on White when 7/7 days reached |
| #4 Reboot recovery | schtasks COM unavailable in sandbox | `python memory/mechanic/deploy_reboot_recovery_all.py` on White (registers FleetBootRecovery x4) |
| #6 Schtask dep graph | schtasks COM unavailable | `python memory/mechanic/schtask_dep_gen.py --weekly` on White |
| #8 Chaos drill | Needs to kill portal process (admin + egress) | `python memory/mechanic/test_chaos_drill_sim.py --live` on White |

## Single unblock command (runs ALL 4 in sequence from White admin):
```
python memory/mechanic/deploy_reboot_recovery_all.py && python memory/mechanic/schtask_dep_gen.py --weekly && python memory/ops/load_trend.py --week-complete
```
(Chaos drill is monthly; run separately when rotation hits.)

## Status: BLOCKED (sandbox COM + egress) - already in blockers.md. Do NOT re-probe from Red sandbox.
