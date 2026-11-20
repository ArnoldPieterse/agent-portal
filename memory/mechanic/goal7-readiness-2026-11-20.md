# Mechanic Goal #7 (Performance Profiling) — readiness check, 2026-11-20

**State: deploy path confirmed-ready; live 1h run BLOCKED from sandbox seat (recorded once in memory/ops/blockers.md).**

What was verified this pass (in-sandbox, real measurements):
- `python -m py_compile memory/mechanic/perf_profile.py` -> COMPILE_OK (207 lines).
- CLI surface complete: `--duration` (default 3600), `--run-once`, `--selftest`, `--verify`, `--portal-url`.
- `--verify` gate is correct: requires non-null p50/p95/p99 for EVERY endpoint AND enforces ordering p50<=p95<=p99 (lines 145-173).
- Selftest logic sound: synthetic 1..100 -> p50=50.5 / p95=95.05 / p99=99.01 assertions.
- `deploy_perf_profile.bat` 3 steps correct: (1) `--duration 3600`, (2) `--verify`, (3) register daily schtask `FleetPerfProfile` @05:00 SYSTEM/HIGHEST.

What is NOT done (cannot be from this seat):
- The live 1-hour collection against localhost:8099. Existing perf-profile.json is a 15s selftest with 0 samples (all p* = null) - not real data.
- Sandbox walls (all pre-documented, NOT re-probed): WinError 10013 egress block to :8099; elev.py absent; schtasks COM "Class not registered".

Single unblock step (non-sandbox White admin terminal with :8099 egress):
    memory\mechanic\deploy_perf_profile.bat
then record: `python memory/researcher/goal_ledger.py --record mechanic 7 --note '...'`
