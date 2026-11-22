# Goal 7 - Log Rotation + Retention

## 2026-11-22T06:50:52.875871+00:00

**Action**: Upgraded `log_rotate.py` to meet all acceptance criteria.

## Changes from previous version
- Threshold: 10MB -> **50MB**
- Scope: `.log` only -> **`.log` + `.jsonl`** across entire fleet tree
- Retention: 5 count-based rotations -> **7-day time-based** with compression
- Added `--dry-run` flag for safe testing
- Evidence logging to `log-rotate-evidence.jsonl`

## Test Results (synthetic 66.8MB file)
| Check | Result |
|-------|--------|
| >50MB file rotated to dated name | PASS |
| Fresh empty file created for new writes | PASS |
| 8-day-old rotation compressed to .gz | PASS |
| Data integrity preserved (70MB intact) | PASS |

## Remaining
- Register as daily schtask on White: `schtasks /create /tn LogRotate /tr "python memory\mechanic\log_rotate.py --once" /sc daily /st 02:00`
- Requires non-sandbox seat with elev.py (current Pale sandbox has egress wall)

## Artifacts
- Script: `memory/mechanic/log_rotate.py`
- Evidence log: `memory/mechanic/log-rotate-evidence.jsonl`
