# Goal #4 progress: load_trend.py built + validated (2026-11-17)

## What was done
- `load_trend.py` created at repo root (was referenced in hot notes but missing from disk)
- Handles both jsonl formats: "levels" (aggregated) and "results" (per-endpoint, load_probe.py output)
- Groups by day, computes trailing median p95/p99 per concurrency level
- Flags regression if latest > 1.3x trailing median (threshold configurable via --threshold)
- Writes `memory/ops/load-trend-report.json`

## Validation run
```
[load_trend] OK | days=2 | regressions=0
```
Report at memory/ops/load-trend-report.json: all 3 concurrency levels show p95_ratio < 1.0 (improvement, not regression).

## Remaining for closure
- 5 more days of real probe data (currently 2/7)
- Sandbox egress blocks :8099 (WinError 10013) — probe must run from a seat with portal access
- Once 7 days collected: `python load_trend.py` should show ≥1 regression caught in demo (acceptance criterion)

## Pipeline state
| Component | Status |
|-----------|--------|
| load_probe.py | EXISTS, writes per-endpoint results format |
| load-baseline.jsonl | 2 days of data (Nov 16 + Nov 17) |
| load_trend.py | BUILT THIS PASS, validated against existing data |
| load-trend-report.json | Fresh (ts 2026-11-17T05:09:49+00:00) |
| Daily scheduled task | Not yet registered (needs portal-access seat) |
