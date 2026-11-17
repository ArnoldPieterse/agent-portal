# Goal #4 - Week-Complete Validation Mode (2026-11-17)

## What was done
Added `--week-complete` flag to `memory/ops/load_trend.py`. When >= 7 days of baseline data exist, it produces a final summary report at `memory/ops/load-week-report.json` with per-concurrency min/max/mean for p50/p95/p99 + total error count + PASS verdict.

## Verification
- `python memory/ops/load_trend.py --week-complete` → exit 1, "only 2/7 days collected - not yet ready" (correct)
- `python memory/ops/load_trend.py` → "load_trend OK (2 days, no regression > 30%)" (unchanged normal mode)

## Impact
Goal #4 closure is now a single command once day 7 data lands from White seat:
```
python memory/ops/load_trend.py --week-complete
```
Then record via ledger.

## Status
- [x] Regression demo caught (synthetic, verified 2026-11-17)
- [x] Week-complete validation mode built + tested
- [ ] 7 days of baseline data collected (currently 2/7; requires White seat daily runs)
