# Goal 7: Performance Profiling - Progress Update (2026-11-20 pass)

## What was done this pass:
1. Added `--verify` mode to `perf_profile.py` - explicit acceptance criteria checker
   - Validates duration >= 60s, all 4 endpoints status=ok, p50<p95<p99 ordering, count>0
   - Exit code 0 on PASS, 1 on FAIL (scriptable for schtask/watchdog)
2. Ran `--selftest` -> PASS (percentile math correct)
3. Ran `--verify` against current perf-profile.json -> FAIL (expected: sandbox dry-run data, 0 samples)

## Remaining for closure (single step):
```
python memory/mechanic/perf_profile.py --duration 3600   # from non-sandbox White seat
python memory/mechanic/perf_profile.py --verify           # must PASS
```

## Blocker:
Sandbox egress wall (WinError 10013 on :8099) + SSPI credential acquisition blocked in sandbox
(SEC_E_NO_CREDENTIALS). WinRM to PALE also fails from sandbox.
Live run requires non-sandbox White interactive terminal.

## Artifact:
- Updated script: memory/mechanic/perf_profile.py (now has --selftest, --verify, --duration modes)
