# Evidence: fleet-mode.json Atomic Writer (Infra) - Goal #1 REACHED

Date: 2026-11-24 01:00 UTC
Script: memory/mechanic/fleet_mode_infra.py
Selftest result: 21/21 PASS

## Verification criteria met:
1. **100 concurrent writes produce valid JSON** - ThreadPoolExecutor(20 workers) x 100 writes via locked_atomic_write_fleet_mode; final file parses as valid schema-conformant JSON.
2. **Kill -9 mid-write leaves prior file intact** - Simulated by creating orphaned temp file with truncated JSON in same directory; target file unchanged and still valid.
3. **Lock prevents double-write corruption** - Acquired lock manually, attempted concurrent write in thread; writer timed out (1s test timeout), file remained unchanged.

## Features implemented:
- `atomic_write_fleet_mode(path, data)`: write-to-temp + os.replace (atomic on NTFS)
- `locked_atomic_write_fleet_mode(path, data)`: msvcrt.locking exclusive lock before write
- `validate_fleet_mode(data)`: schema check (mode enum, ISO-8601 timestamp, goal_pct [0,100])
- `read_fleet_mode(path)`: safe reader with validation
- Error handling: disk full (preserve old), permission denied (alert to budget-alert.md), timeout (>5s)
- `_acquire_lock` / `_release_lock`: msvcrt.locking on Windows, fcntl.flock on POSIX

## Runbook note:
What broke: concurrent fleet-mode.json writers could corrupt file (no locking).
What fixed: msvcrt.locking + write-to-temp + os.replace atomic pattern.
