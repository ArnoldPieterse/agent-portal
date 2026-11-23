# Evidence: auto_quarantine.py selftest fix (2026-11-23)

## Issue
Self-test was failing 4/7 checks because the test file was created fresh (mtime=now),
so `run_quarantine()` recalculated its score as ~1.0 (above threshold), which reset
the manually-set below_threshold_streak before quarantine could trigger.

## Fix
Added `os.utime(test_path, (old_ts, old_ts))` to set mtime 20 days back,
making computed score = max(0.05, 1.0 - 20*0.03) = 0.4 < threshold 0.5.

## Result
`python memory/archivist/auto_quarantine.py --test` → 7/7 PASS (was 2/6 before fix;
the 6th check "Content preserved" was previously skipped because file wasn't quarantined).

## Verification command
```
python memory/archivist/auto_quarantine.py --test
```
Exit code: 0. Output: "Result: 7/7 checks passed"

Timestamp: 2026-11-23T10:02Z
