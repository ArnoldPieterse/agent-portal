# Goal 2 (Self-Healing Mirror) - DEPLOY-READY Consolidated (2026-11-23)

**Purpose:** single copy-paste artifact for whoever regains White access. All code ACs verified; only the schtask registration + 2-week log window remain, both requiring White (elev.py exit 5 in this seat = pale-sandbox COM class unavailable, NOT fixable from here - see memory/ops/blockers.md).

## Canonical module (confirmed this pass)
- Path: `memory/ops/mirror_heal.py` (NOT under mechanic/; selftest adds memory/ops to sys.path)
- Constants: `MAX_AGE_S = 900` (15 min), `ALERT_THRESHOLD = 3` (alert when >3 failures in last hour)
- Repair log: `memory/mechanic/mirror-repairs.jsonl`

## Acceptance criteria status
| Criterion | Status |
|-----------|--------|
| Detect missed syncs, re-sync automatically | PASS (dry-run fires STALE at age>900s; repair path logs repair_ok/repair_failed) |
| Alert only on >3 failures in an hour | PASS (selftest: 3->no alert boundary, 4+->ALERT True with failures_last_hour + alert_msg) |
| Two weeks of clean repair logs | PENDING (needs White + time; clean since ~Nov 17) |
| schtask registered on White | PENDING (below one-liner) |

## Fresh verification run (this pass, 2026-11-23)
```
$ python memory/mechanic/goal2_mirror_heal_selftest.py
RESULT: 17 PASS / 0 FAIL out of 17
ALL TESTS PASSED
```
Also `python memory/mechanic/test_mirror_heal_logic.py` = 9/9 (current API).

## One-liner to close the registration leg (run ONCE on White, admin via elev.py)
```
python elev.py --shell "schtasks /create /tn MirrorHeal /tr \"python memory\\ops\\mirror_heal.py\" /sc minute /mo 15"
```
Or batch: `python memory/mechanic/deploy_all_schtasks.py` (includes MirrorHeal + LogRotateDaily).
After registration, closure = two weeks of clean mirror-repairs.jsonl with zero unexplained drift >5 min.

**Credit:** Mechanic (evidence/ledger upkeep pass; no re-probe of the elev.py wall).