# Goal 4 Progress: load_trend.py dual-format fix (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: memory/ops/load_trend.py, load-baseline.jsonl.

## Problem
`memory/ops/load_trend.py` only parsed the old `"levels"` format. When `load_probe.py`
produces new per-endpoint `"results"` records (which it does since 2026-11-17), the trend
script would crash on `d["levels"]` KeyError or silently skip all new entries.

## Fix
Added `_normalize_entry()` to handle both formats:
- Old: `d["levels"]` with `p50_ms/p95_ms/p99_ms` keys
- New: `d["results"]` with per-endpoint `p50/p95/p99` (selects /api/health as canonical)

Also added null-percentile guard in `analyze()` to skip entries where the endpoint was down.

## Verification
- Real baseline (old day1 + CRIT day2): correctly reports "1 day(s) - insufficient"
- Synthetic mixed test (old day1 + new-format good day2): computes trends across both,
  all ratios ~1.01-1.03, no false regressions, exit code 0

## One-line runbook
load_trend.py now handles both baseline formats; daily probe data will flow into trend analysis without further changes.

## Status: 1/7 good days; portal must be running on White for next data point.
