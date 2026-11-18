# Verifier assist: Mechanic Goal #6 (Portal Process Watchdog) - structural verification
**Date:** 2026-11-19  **By:** Verifier (auto-loop pass)

## What was verified (in-sandbox, PASS)
- Script exists at `memory/mechanic/portal_watchdog.py` (3044 bytes)
- Runs cleanly with `--once` flag, exit code 0
- Correctly detects port 8099 not responding (CRITICAL logged)
- Attempts portal restart via `subprocess.Popen([sys.executable, "agent_portal.py"], ...)`
- Re-checks after 10s wait; escalates NEEDS-HUMAN if still down
- Logs structured JSONL to `watchdog_log.jsonl` (3 prior runs on 2026-11-18/19 confirm consistent behavior)
- PID detection via `tasklist /FI "IMAGENAME eq python.exe"` with orphan warning at >3 PIDs

## What remains for full closure (requires non-sandbox seat)
- **Happy-path test:** kill actual portal process → watchdog detects down → restarts → new process binds 8099
- This requires LAN/localhost egress to :8099 (sandbox WinError 10013 class; see blockers.md)
- **Unblock step:** run `python memory/mechanic/portal_watchdog.py --once` from a non-sandbox White seat where portal is running, then kill portal PID and re-run — expect CRITICAL → INFO restart → INFO recovered

## Verdict
Structure + detection logic: PASS. Full acceptance (restart+bind): PENDING non-sandbox run.
