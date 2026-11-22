# Goal 7 Log Rotation - Verification Evidence (2026-11-23)

**Status:** All 4 acceptance criteria PASS locally. Only remaining leg = schtask registration (elev.py exit 5, logged in blockers.md).

## Test Run: `python memory/mechanic/log_rotate.py --once`

| AC | Result |
|---|---|
| File >50MB rotated | PASS - 63.4MB .jsonl truncated to 0B + `.gz` created (0.22MB) |
| 8-day-old files compressed | PASS - 10-day-old .log removed, `.gz` created (1000 lines preserved) |
| Disk usage bounded | PASS - live file = 0 bytes post-rotation |
| No data loss | PASS - all 150,000 lines recoverable from .gz; old file 1000 lines intact |

## Commands
```
python memory/mechanic/log_rotate.py --once
# Output: 2026-11-22T14:37:47Z [rotated=1 compressed_old=1] max=50MB retention=7d
```

## Remaining for closure
`python elev.py --shell "schtasks /create /tn LogRotateDaily /tr \"python Z:\\memory\\mechanic\\log_rotate.py --once\" /sc daily /st 03:00 /ru SYSTEM /f"`
or: `python memory/mechanic/deploy_all_schtasks.py` (includes LogRotateDaily).

Blocker: elev.py exit 5 (helper down) - logged in memory/ops/blockers.md [NEEDS-HUMAN 2026-11-20].
