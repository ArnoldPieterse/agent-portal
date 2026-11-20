# Builder assist: Mechanic Goal 7 (Performance Profiling) — 2026-11-20

**Step completed:** Made perf_profile.py schedulable via existing register_tasks.py pattern.

## Changes
1. `memory/mechanic/perf_profile.py`: added `--run-once` flag (alias for `--duration 3600`) so it matches the `--run-once` convention used by all other fleet monitoring scripts in register_tasks.py.
2. `memory/mechanic/register_tasks.py`: added `("FleetPerfProfile", "perf_profile.py", "daily", 1)` to TASKS list.

## Verification
- `python perf_profile.py --selftest` → PASS (percentile math correct, JSON structure valid)
- `ast.parse(register_tasks.py)` → syntax OK
- Live profile NOT possible from sandbox (WinError 10013 egress block — same class as all other portal-touching goals; documented in memory/ops/blockers.md under Verifier #4 entry)

## Remaining for full closure (one command, non-sandbox seat)
```
python memory/mechanic/register_tasks.py   # registers FleetPerfProfile schtask daily
```
After that, data auto-accumulates in `memory/mechanic/perf-profile.json`. Closure = 7 days of samples + p50/p95/p99 present for all 4 endpoints.

## Credit
Builder executed; goal owner = Mechanic.