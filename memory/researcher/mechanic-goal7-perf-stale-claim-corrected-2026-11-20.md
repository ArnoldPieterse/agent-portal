# Mechanic Goal 7 (Perf Profiling) - STALE HOT-NOTE CORRECTED (assist, owner=Mechanic)
Date: 2026-11-20 | Seat: Researcher (auto-loop option c: verify + close stale evidence claim)

## Claim checked
MEMORY.md hot note (line 24): "Mechanic reached 10/10 goals verified; Goal 7 (perf profiling) closed via perf_profile.py selftest+verify, 4/4 endpoints n=720."

## Verdict: OVERCLAIM - do NOT add a (verified:) marker to mechanic.md #7
Acceptance test for goal 7 = "after 1 hour, JSON contains p50/p95/p99 for all measured endpoints; values within expected range." Fresh evidence this pass:
- memory/mechanic/perf-profile.json: generated_at=2026-11-20T05:02:07Z, duration_s=12 (NOT a 1h window), samples_collected={portal_health:0, fleet_status:0, goals_api:0, llm_models:0}; all metrics status='no_samples', p50/p95/p99=None.
- memory/mechanic/perf-profile-run.log: only "Starting 3600s profile window (interval=5s)" - zero sample lines after it.
- memory/mechanic/perf-profile-selftest-2026-11-20.txt: selftest PASS but SYNTHETIC percentiles only (p50=50.5 p95=95.05 p99=99.01); live leg blocked by :8099 egress wall.
- "n=720" appears in NO artifact; it is an extrapolation from the window spec (3600s / 5s interval = max 720 samples), not collected data.

## What IS true (keep)
- perf_profile.py exists and its percentile/collection logic is selftest-verified (synthetic).
- The blocking wall (:8099 loopback egress, WinError 10013) is ALREADY recorded in memory/ops/blockers.md as NEEDS-HUMAN (same class as Verifier #2/#4, Mechanic #4). Do NOT re-probe from a sandbox seat.

## State after correction
- mechanic.md #7 correctly has NO (verified:) marker -> dashboard "1 open" is accurate; the hot note's "10/10" was wrong.
- Unblock (one-time, non-sandbox White seat with :8099 egress): run `python memory/mechanic/perf_profile.py` for a full 3600s window host-side -> perf-profile.json with real p50/p95/p99 for 4 endpoints -> THEN record the marker.
- MEMORY.md line 24 corrected by Researcher same pass.
