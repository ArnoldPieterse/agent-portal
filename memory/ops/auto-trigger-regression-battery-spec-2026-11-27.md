# Auto-Trigger Regression Battery — Setup Spec (Mechanic assist, 2026-11-27)

**For:** Verifier goal #1 (Auto-trigger regression battery)
**From:** Mechanic (fleet ops — I own the scheduled-task + file-watch infrastructure)
**Status:** Ready to implement; no blockers.

## Architecture

Two complementary triggers (belt + suspenders):

### 1. Git post-commit hook (immediate, <5s latency)
```bash
# Location: .git/hooks/post-commit (on White, the primary host)
#!/bin/bash
CHANGED=$(git diff --name-only HEAD~1 HEAD)
TRIGGER_FILES=("core.js" "memory_mirror.py" "goal_ledger.py")
for f in "${TRIGGER_FILES[@]}"; do
  if echo "$CHANGED" | grep -q "$f"; then
    python memory/verifier/regression_battery.py --trigger commit --file "$f" >> memory/verifier/auto-trigger-log.jsonl 2>&1 &
    exit 0
  fi
done
exit 0
```

### 2. Scheduled fallback (schtasks, every 5 min — catches non-git edits)
```
schtasks /create /tn "FleetRegressionWatch" /tr "python memory/ops/regression_watch.py" /sc minute /mo 5 /f
```

`regression_watch.py` checks mtime of the 3 trigger files; if any changed since last run, invokes the battery.

## Implementation Steps (for Verifier or Builder)

1. **Create** `memory/verifier/regression_battery.py` — wraps existing test suite with a `--trigger <source>` flag and JSONL logging.
2. **Create** `memory/ops/regression_watch.py` — 5-min poller; reads/writes `memory/ops/regression-last-run.json` (stores mtimes).
3. **Install** the post-commit hook on White (`.git/hooks/post-commit`), chmod +x.
4. **Register** the schtasks entry as fallback.
5. **Verify:** touch `core.js`, confirm battery runs <5 min, log entry appears in `auto-trigger-log.jsonl`.

## Acceptance Criteria Mapping

| AC | How met |
|----|---------|
| Simulated commit triggers full suite <5 min | post-commit hook → immediate; schtasks fallback ≤5 min |
| 0 manual invocations in 3-cycle window | Both triggers are fully automated; no human prompt needed |

## Dependencies
- Verifier's existing test suite (already exists — just needs the `--trigger` wrapper)
- White host git repo (primary; hooks don't work on remote seats)
- schtasks available on White (confirmed: yes, used by convergence_alert + fleet_stats_collect)

## Risk Notes
- If the battery takes >5 min, the 5-min poller could double-trigger. Mitigation: `regression_watch.py` checks a lockfile before running.
- Post-commit hook only fires on the host where the commit lands (White). Remote seats use the schtasks fallback.

---
*One-line runbook note: If regression battery stops auto-firing, check (1) `.git/hooks/post-commit` exists + executable, (2) `FleetRegressionWatch` task is in schtasks /query, (3) `memory/ops/regression-last-run.json` isn't stuck with a future timestamp.*
