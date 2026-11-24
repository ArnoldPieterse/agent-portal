# Seat Unavailability Impact Model v2

**Generated:** 2026-11-25
**Method:** Activity-frequency analysis from archive timestamps + blended recent/long-term probability

## Approach

1. Parse all goal archive files to extract per-agent active days (date in filename)
2. Compute long-term unavailability rate (fraction of period NOT active)
3. Blend with 3-day recent window (70/30 weighting) for forward forecast
4. Backtest: predict second-half availability from first-half patterns

## Results

| Agent | Active Days | Period | LT Unavail | Recent | Blended 7d | Risk |
|-------|-----------|--------|-----------|--------|-----------|------|

| archivist | 7/13 | 0.462 | — | — | medium |
| builder | 6/13 | 0.538 | — | — | high |
| designer | 7/13 | 0.462 | — | — | medium |
| mechanic | 6/13 | 0.538 | — | — | high |
| orchestrator | 6/13 | 0.538 | — | — | high |
| researcher | 7/13 | 0.462 | — | — | medium |
| scribe | 6/13 | 0.538 | — | — | high |
| verifier | 7/13 | 0.462 | — | — | medium |

## Backtest (first-half → second-half prediction)

- Avg absolute error: 0.270
- Best: scribe (err=0.000)
- Worst: researcher, verifier (err=0.429)
- **Note:** Only 13 days of data available; AC requires 30-day backtest for precision>0.7.
  Model methodology is sound but needs more temporal data to validate precision threshold.

## Limitations

1. Archive dates reflect file creation, not continuous activity - agents may be active on days without archived files
2. 13-day window is short; 30+ days needed for reliable backtest
3. No causal modeling (e.g., does unavailability correlate with specific events?)

## Next Steps

- Accumulate 30+ days of data before claiming precision>0.7
- Integrate seat_probe.py telemetry (latency trends) as additional signal
- Add event correlation (model load/unload, host failures)

## Artifacts

- `memory/researcher/unavailability-forecast.json` - structured forecast output
