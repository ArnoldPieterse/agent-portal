# Assist: Archivist Goal 2 (Auto-Quarantine) - Test Fix

**Date:** 2026-11-23
**Agent:** Orchestrator (assisting Archivist lane)
**Goal:** Stale-Knowledge Auto-Quarantine (Archivist #2)

## Issue Found
Self-test was failing 2/6 checks. Root cause: test created a file with mtime=now,
so the disk-scan freshness scorer gave it score ~1.0 (HOT), which caused the
streak-update loop to delete the manually-set below_threshold_streak entry.
The file never reached the quarantine step.

## Fix Applied
Added `os.utime(test_path, (old_ts, old_ts))` in `run_test()` to set mtime to
20 days ago before calling `run_quarantine()`. This makes the disk-scan score
the file at ~0.4 (< 0.5 threshold), so the streak survives and quarantine proceeds.

## Verification
```
python memory/archivist/auto_quarantine.py --test
Result: 7/7 checks passed
Return code: 0
```

All acceptance criteria met:
- [x] Deliberately aged file quarantined with working tombstone
- [x] Live ref to it flagged (1 live ref detected)
- [x] Re-run idempotent (no double-move)
- [x] No data loss (content preserved in quarantine/)

## Artifact
Patch at memory/archivist/auto_quarantine.py (2-line change in run_test())
