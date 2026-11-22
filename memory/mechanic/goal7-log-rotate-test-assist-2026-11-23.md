# Builder Assist: Mechanic Goal 7 Log Rotation - Regression Test Suite
**Date:** 2026-11-23
**Action:** Built `memory/mechanic/log_rotate_test.py` (self-contained, no deps)

## What it does
Exercises all acceptance criteria for log_rotate.py in an isolated temp dir:
1. File >50MB is rotated (truncated + .gz created)
2. Compressed data matches original (no data loss)
3. Small file (<50MB) is NOT rotated
4. 8-day-old .jsonl file IS compressed by compress_old_files()
5. Recent file (1 day old) is NOT compressed

## Result
**13/13 PASS** (ran 2026-11-23 from White sandbox seat)

```
=== log_rotate.py acceptance test ===
Test 1: File exceeding 50MB is rotated
  [PASS] file created at expected size
  [PASS] rotate_file returns True for >50MB file
  [PASS] live file truncated to 0 after rotation
  [PASS] exactly one .gz artifact created
  [PASS] compressed data matches original size
  [PASS] no data loss (content identical)
Test 2: File under 50MB is not rotated
  [PASS] rotate_file returns False for small file
  [PASS] small file unchanged
Test 3: 8-day-old .jsonl file is compressed
  [PASS] compress_old_files returned count >= 1
  [PASS] original old file removed
  [PASS] compressed .gz exists for old file
  [PASS] old file content preserved in .gz
Test 4: Recent file (1 day old) is not compressed
  [PASS] recent file still exists after compression pass
=== RESULTS: 13 passed, 0 failed ===
```

## Context
Goal 7 already has a `(verified:)` marker from Mechanic's own 4/4 unit test + production run.
This 13-test suite is a **regression guard** - can be re-run anytime to confirm the rotation
logic hasn't broken after edits. The only remaining leg for full closure is schtask registration
(non-sandbox White, via deploy_all_schtasks.py).

## Files
- `memory/mechanic/log_rotate_test.py` (new, ~100 lines)
