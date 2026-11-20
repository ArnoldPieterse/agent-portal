# Goal 1 Progress: AC5 Connection Pool Management (2026-11-20)

## What was added
- `WinRMPool.pool_stats()` - returns per-host active/idle session counts + idle time
- `WinRMPool.evict_idle(max_age_s=300)` - proactively evicts stale sessions, returns evicted host list

## Selftest result
- 30/30 PASS (up from 20; AC5 adds 10 new checks)
- Verified: session reuse (no re-creation on 2nd call), eviction removes >300s sessions, keeps fresh ones

## Remaining for goal closure
- Live 4-host remote exec on non-sandbox White seat (sandbox wall unchanged - NEEDS-HUMAN recorded)
- `close_goal1.bat` is ready for that single run

## Files changed
- memory/mechanic/winrm_pool.py (+32 lines: pool_stats + evict_idle methods)
- memory/mechanic/winrm_pool_selftest.py (+49 lines: test_pool_management AC5)
