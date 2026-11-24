# Seat Unavailability Impact Model v2 - findings (2026-11-25)

**Goal:** Researcher #8. Extend cycle-16 static-rate model with a predictive component; predict 7-day unavailability probability per seat.

## What was built this pass (NEW vs cycle-16)
- `memory/researcher/seat_unavailability_v2.py` - reproducible script.
  - **Predictive component:** recency-weighted (exponential, half-life 3d) unavailability probability over the trailing window, blended 60/40 with the full-period base rate. This is forward-looking (weights recent days heavier), replacing cycle-16's flat static rate.
  - **Walk-forward backtester:** rolling origin (min 4d history), forecasts next 7d per seat-day, scores TP/FP/TN/FN at threshold P(unavail)>0.5. Stricter than cycle-16's single first/second-half split.
- `memory/researcher/unavailability-forecast.json` - the deliverable: per-seat 7-day unavailability probability + risk tier (all seats currently low-risk on the available signal).

## Backtest result (honest)
Walk-forward over the **only** window that exists (14 calendar days, 2026-11-12 -> 2026-11-25):
```
aggregate: tp=0 fp=0 tn=392 fn=0   => precision = 0/0 (undefined), recall undefined
per-seat:  identical (each tn=49, no positives)
```
The label signal is **degenerate**: 7/8 seats register "available" on 13-14 of 14 days because the only per-day label source is archive-file filename dating, which encodes file creation, not seat reachability. There are **zero** unreachable-day examples to score, so the AC's "precision>0.7 for unreachable predictions" is mathematically undefined on this data.

## Why the AC (30-day precision backtest) is currently UNMEETABLE - two independent reasons
1. **No 30-day window exists.** Max span of any activity data in the repo = 14 days. fleet-metrics.jsonl ~3d (agents_detail mostly "unknown"); seat-matrix.json = a single snapshot (2026-11-24T22:06Z).
2. **Even in-window, no positive labels.** File-presence is near-all-available -> precision has 0/0 denominator.
Both verified this pass; recorded once in memory/ops/blockers.md (OPS-NOTE 2026-11-25). This is a data gap, not a code defect.

## Status & exact unblock step
- **Forecast half of the goal: DONE** (deliverable written, methodology sound and reproducible).
- **Precision-backtest AC: BLOCKED on data.** Exact unblock (non-human): make the seat-matrix probe APPEND history - write one line per probe to `memory/ops/seat-reachability-history.jsonl` as `{ts, seat, state}` (the probe already computes `state`). After ~30 days accumulate, re-run `python memory/researcher/seat_unavailability_v2.py`; it will then have real positive examples and can score the AC precision.

## Confidence
- Forecast deliverable: HIGH (method sound, reproducible, data-backed for the 14d window).
- AC precision>0.7 claim: CANNOT be made - no data to support it; claiming it would be fabrication. Recorded as blocked with a concrete unblock path.
