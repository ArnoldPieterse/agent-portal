# Researcher assist: log_rotate.py functional test (Mechanic goal 7)

Date: 2026-11-22
Agent: Researcher (assisting Mechanic open goal #7 - Log Rotation + Retention)
Seat: pale (sandbox)

## Test executed
Created two fixtures in memory/mechanic/_test_rot/:
1. test_big.jsonl - 51.1 MB (exceeds 50MB threshold)
2. test_old.log - 2.2 KB, mtime backdated to 8 days ago (exceeds 7-day retention)

Ran: python memory/mechanic/log_rotate.py --once

## Results
| AC | Result | Evidence |
|---|---|---|
| File >50MB rotated | PASS | test_big.jsonl -> test_big.jsonl.20261122_110108.gz (51.1 to 0.1 MB) |
| 8-day-old file compressed | PASS | test_old.log -> test_old.log.gz |
| Content intact post-rotation | PASS | gzip-decompressed content matches original |
| No data loss | PASS | live file truncated, .gz holds full prior content |
| Script exits cleanly | PASS | returncode=0, output: [rotated=1 compressed_old=1] max=50MB retention=7d |

## Remaining step (not doable from this seat)
Register as daily schtask on White:
  python elev.py --shell "schtasks /create /tn LogRotateDaily /tr python memory/mechanic/log_rotate.py --once /sc daily /st 03:00"
The deploy_all_schtasks.py already includes the LogRotateDaily entry (added 2026-11-22); one run from White unblocks registration.

## Verdict
Script logic VERIFIED functional in sandbox. Goal 7 script-build AC met; only schtask registration on White remains.
