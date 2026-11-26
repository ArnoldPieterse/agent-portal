# Mirror Sync Recovery Runbook

## Trigger
Mirror sync lag > 10 min sustained (2 consecutive checks).

## Steps
1. Check mirror process: `tasklist | findstr python` for memory_mirror.py
2. If not running: restart via scheduled task or manual launch
3. Force immediate sync: `python memory_mirror.py --once`
4. Verify: check mtime of mirrored files; should be < 1 min after sync
5. Log recovery to memory/ops/runbook-executions.jsonl

## Prevention
- Scheduled task runs mirror every 5 min
- Drift monitor checks every probe cycle (60s)
