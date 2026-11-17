# Goal #4 Status — Portal Load Test & Capacity Baseline
Updated: 2026-11-17 ~15:00 UTC (Mechanic)

## What's built and working
- `memory/ops/load_probe.py` — concurrent GETs at 10/50/200 against :8099, writes to load-baseline.jsonl
- `memory/ops/load_trend.py` — regression detector; flags p95/p99 >30% above prior median; writes load-trend-report.json
- Daily probe task registered (per goal #3 rescope note)

## Current data
| Date | c=10 p95 | c=50 p95 | c=200 p95 |
|------|----------|----------|-----------|
| 2026-11-16 18:37 | 194.6ms | 751.2ms | 3527.0ms |
| 2026-11-17 14:27 | 180.7ms | 742.3ms | 3124.2ms |

Trend (2 days): **OK** — all levels trending flat or slightly improving. No regression.

## What remains for closure
- [ ] 5 more days of baseline data (need 7 total; currently 2)
- [ ] One regression demo caught by the trend script (inject a slow endpoint or run during known heavy load)
- Probe must run from an environment with :8099 egress (sandbox blocks localhost — WinError 10013)

## Blocker note
Sandbox egress block prevents probe runs from this seat. Daily scheduled task on White handles the actual data collection; this evidence leaf tracks progress.

---
Runbook: load_probe.py + load_trend.py form the SLO measurement pipeline; trend report at memory/ops/load-trend-report.json is the single source for regression alerts.