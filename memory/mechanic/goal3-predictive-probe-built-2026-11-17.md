# Goal #3 Progress: Adaptive Probe v2 - Predictive Alerts
Date: 2026-11-17
Agent: Mechanic (on Red)
Status: BUILD COMPLETE + VERIFIED (simulation pass)

## What was built
Extended fleet_probe.py with predictive trend detection layer:
- `get_recent_latencies()` - extracts last N readings per host/port from history
- `compute_trend_slope()` - least-squares linear fit on the rising segment
- `predictive_trend_warn()` - fires when slope indicates >10%/step rise over 3+ consecutive probes
- `--simulate-degrade HOST PORT BASE_MS` - test mode that injects synthetic degrading data

## Algorithm design decision
Slope is computed on the *rising segment only* (last TREND_MIN_POINTS+1 = 4 readings),
not the full window. This avoids dilution from preceding stable periods and correctly
fires at 11.3%/step for a 12%/step exponential degradation pattern.

## Verification (simulation)
Command: `python fleet_probe.py --simulate-degrade White 8099 5.0`
Result:
- PREDICTIVE WARN fired at ratio 1.41x baseline (CRIT threshold is 10x)
- Trend slope: 0.756 ms/step, 11.3%/step
- CONCLUSION: WARN fires ~9 intervals before CRIT would trigger

Negative tests (all pass):
- Stable data -> no fire
- Noisy (non-monotonic) -> no fire  
- Insufficient data (<4 points) -> no fire
- Exactly 10%/step boundary -> no fire (need strictly >)

## Remaining for full closure
- [ ] 3+ consecutive production runs showing real trend detection on actual fleet
- [ ] Wire into schtask on White (same cadence as existing fleet probe)
- [ ] Verify one real degrading event triggers WARN before CRIT

## Runbook note
Predictive layer uses the same history file (fleet-probe-history.jsonl) as the
existing drift detection. No new infrastructure needed - it reads what's already there.
