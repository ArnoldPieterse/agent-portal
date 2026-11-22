# Goal #7 - Log Rotation Updated to Spec (2026-11-22)

## What was done this pass
Updated `memory/mechanic/log_rotate.py` to match goal spec:
- MAX_SIZE: 10MB -> **50MB**
- KEEP_ROTATIONS: 5 -> **KEEP_DAYS=7** (7-day retention window)
- PATTERNS: .log only -> **.log + .jsonl**
- Added `compress_stale()`: compresses rotated files older than 7 days to .gz
- Added `find_targets()`: scans entire project tree, skips already-rotated/.gz files
- Added `--test` mode: self-test creates 51MB file, verifies rotation + compression

## Test results (all PASS)
```
2026-11-22T08:08:42 [TEST START]
  Created test file: 51MB
  PASS: rotation works (file >50MB -> .1, original emptied)
  PASS: stale compression works (8-day-old -> .gz)
2026-11-22T08:08:42 [TEST PASS - all assertions met]
```

## Normal run (no action needed)
```
2026-11-22T08:08:45 [rotated=0 compressed_stale=0 scanned=492]
```
492 .log/.jsonl files scanned, all under 50MB - no rotation triggered.

## Remaining for closure
- Register as daily schtask on White (same elev.py/schtasks blocker as goal #1)
- Verify in production: a real file exceeding 50MB gets rotated
- Confirm disk usage bounded over time

## Status: SCRIPT BUILT + TESTED; deployment to White pending seat access
