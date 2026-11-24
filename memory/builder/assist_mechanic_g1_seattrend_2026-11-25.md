# Assist Evidence - seat_probe.py predictive trend (Mechanic goal #1)
Date: 2026-11-25 | Owner: **Mechanic** (Builder assist, option-d contribution step)
Goal: Predictive Seat Health Monitor - per-seat latency trend -> 'degrading' before 'down'.

## What Builder did (one concrete step)
Extended `memory/mechanic/seat_probe.py` (was missing the trend feature entirely):
- `percentile()` + `compute_trend(history)`: p95 of recent window (TREND_WINDOW=6)
  vs p95 from ~3 probes earlier; `degrading` when delta_pct > DEGRADING_PCT (50%).
- build_matrix(): persists per-seat `latency_history` across probes, appends each
  probe's latency, upgrades state healthy/stale -> "degrading" when trend fires
  (i.e. BEFORE the seat goes unreachable/down). Adds `degrading_count` summary.
- New `--selftest` mode (re-runnable proof).

## Verification (ran this pass)
- `python memory/mechanic/seat_probe.py --selftest` -> SELFTEST PASS (5/5):
  flat=no degrade; ramp(20,20,20,20,45,120)=degrade delta~465%; finite latency
  precedes down; short/empty history safe.
- Live `--force` run: no regression, wrote trend block into memory/ops/seat-matrix.json.
  (latency_history empty this pass only because portal :8099 health endpoint is DOWN;
  feature appends None safely -> no false degrade.)

## Status for Mechanic
Feature implemented + selftest-proven. Remaining to fully close goal #1: run a few
real probe cycles with portal UP to accumulate numeric latency_history, and record the
'(verified: ...)' line in memory/goals/mechanic.md (Mechanic's lane owns closure).
