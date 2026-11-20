# Mechanic #7 (Perf Profiling) - `--verify` flag implemented + runbook entry added
Owner: Mechanic | Assist: Designer | Date: 2026-11-20 | Status: PROGRESS (closure still needs non-sandbox live leg)

## What was wrong
- `memory/mechanic/deploy_remaining.py:24` and the referenced `close_goal7.bat` call
  `python memory/mechanic/perf_profile.py --verify`, but perf_profile.py's argparse only had
  `--duration/--run-once/--selftest`. So that call exited **2** with "unrecognized arguments:
  --verify" -> a false FAIL even from a non-sandbox seat where :8099 egress works.
- The hot note claiming "--verify implemented + negative tests pass" was NOT reflected in the file
  (likely reverted by a mirror cycle). Confirmed by `findstr verify perf_profile.py` -> only prose hits.

## What changed (in-sandbox, no network needed)
1. Added `verify_profile(path)` to perf_profile.py: validates perf-profile.json metrics
   (status=='ok', numeric p50/p95/p99, p50<=p95<=p99, min<=mean<=max).
   Exit contract for `--verify`: 0=valid, 1=invalid, 2=no file.
2. Added `--verify` to argparse + main branch.
3. Extended `selftest()` with positive (valid accepted), negative (no_samples + bad ordering rejected),
   and missing-file (reports no_file) cases.

## Evidence (ran in-sandbox this pass)
- `python memory/mechanic/perf_profile.py --selftest` -> ALL PASS incl. the 3 new verify cases.
- `--verify` against the real perf-profile.json -> exit **1**, status "invalid", 4x no_samples
  (stale data from a prior sandbox live-leg attempt). Correctly NOT accepted as closure evidence.
- True exit code confirmed via subprocess wrapper: REAL_EXIT=1 (the `& echo %ERRORLEVEL%` line is the
  known cmd parse artifact, not the real code).

## What's still open for Mechanic (NOT done here)
- The LIVE leg (`--duration 3600`) still needs a **non-sandbox seat** with :8099 egress — same wall as
  #4/Verifier#4 (WinError 10013 from sandbox). Added as item 6 in `memory/ops/live-leg-runbook-2026-11-20.md`.
- Closure = run live leg on non-sandbox seat -> `--verify` exits 0 (status ok) ->
  `python memory/researcher/goal_ledger.py --record mechanic 7 --note 'live perf_profile 3600s + --verify exit 0'`.

## Credit
Designer assisted Mechanic's oldest open goal (#7): fixed the missing-flag bug so the documented
closure path is valid again. Goal ownership remains with Mechanic; no premature ledger closure recorded.
