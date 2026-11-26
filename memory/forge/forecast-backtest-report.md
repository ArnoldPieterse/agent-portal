# Forecast-Calibration Backtest (Forge goal #8)

Run: 2026-11-26T23:32:53.241572

## Part 1 - Real calibration track record (measured, no simulation; informational)
- snapshots replayed: **108** across **4** cycle-days (all available history)
- live-forecaster Brier curve (day -> mean Brier, n):
  - 2026-11-23: Brier=0.1438 (n=223)
  - 2026-11-24: Brier=0.1385 (n=260)
  - 2026-11-25: Brier=0.3447 (n=209)
  - 2026-11-26: Brier=0.3163 (n=126)

Per-lane measured base-rate + bias (seeds the A/B world):
  - archivist: base_rate=0.0261 bias=0.3908 (n=153)
  - builder: base_rate=0.2128 bias=0.1335 (n=94)
  - designer: base_rate=0.0 bias=0.076 (n=93)
  - forge: base_rate=0.1081 bias=0.3796 (n=37)
  - mechanic: base_rate=0.0 bias=0.4226 (n=80)
  - orchestrator: base_rate=0.5319 bias=-0.1596 (n=47)
  - outlet: base_rate=0.0 bias=0.4148 (n=53)
  - researcher: base_rate=0.2785 bias=-0.1682 (n=79)
  - scribe: base_rate=0.7937 bias=-0.2221 (n=63)
  - verifier: base_rate=0.0 bias=0.5244 (n=115)

## Part 2 - A/B feedback backtest (residual loop via forecast_calibration)
- cycles: **10** | 8 goals/lane/cycle | top-K dispatch K=40 of 80 | seed=20261126
- mean Brier  baseline=0.1948  feedback=0.1234  (Δ=0.0714)
- mean top-K precision  baseline=0.1775  feedback=0.3175  (Δ=0.14)
- Brier curves: baseline=[0.1973, 0.1983, 0.211, 0.1835, 0.2015, 0.1816, 0.1907, 0.1856, 0.2082, 0.1899]
                feedback=[0.1973, 0.0904, 0.1368, 0.1255, 0.1316, 0.1022, 0.1152, 0.1043, 0.123, 0.1076]

> Acceptance: A/B on >=6 cycles with feedback precision > baseline + Brier curves written. A/B ran **10** cycles.

**RESULT: PASS**