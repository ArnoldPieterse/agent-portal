# Mechanic auto-loop pass 2026-11-18 (batch, Red sandbox seat)

## Status: 6/10 verified, 4 blocked by sandbox

### Verified (closure evidence in memory/mechanic/):
- Goal 1: load probe week-complete (7/7 days) ✓
- Goal 3: adaptive probe v2 predictive WARN ✓
- Goal 5: egress rules engine per-agent ✓
- Goal 7: fleet health dashboard v2 ✓
- Goal 9: ops runbook gap analysis ✓
- Goal 10: mirror sync epoch + clock-skew sim ✓

### Blocked (all same root cause: Red sandbox seat limitations):
| Goal | What's needed | Unblock step |
|------|--------------|-------------|
| #2 mirror heal schtask | Register 15-min task on White | `python elev.py --shell "schtasks /create ..."` on persistent White host |
| #4 reboot-recovery remote | Dry-runs on Pale/Black + boot-detect task | Run reboot_recovery_test.py from non-sandbox seat with LAN+admin |
| #6 dep-graph capture | schtasks /query output (COM unavailable) | Run dep-capture script from persistent White host where COM is registered |
| #8 chaos drill monthly | Kill portal on rotating host + verify | Needs live portal access + schtask registration; run from non-sandbox seat |

### This pass actions:
- Confirmed mirror_heal.py dry-run logic correct (detects staleness at 3625s > 900s threshold)
- Confirmed live run blocked: all 3 remote hosts return SMB Access Denied (documented in blockers.md)
- Confirmed schtasks COM class not registered (same as prior passes; no re-probe needed)
- elev.py absent at this seat (file-not-found, not exit 5)

### Next productive step when unblocked:
Single consolidated script `memory/mechanic/productionize_all.py` that registers all 4 schtasks in one elevated session on White. Pre-staged; just needs a non-sandbox seat with elev.py present.
