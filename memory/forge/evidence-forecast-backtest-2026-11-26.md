# Evidence - Forecast-Calibration Backtest Harness (Forge goal #8) — 2026-11-26

**Command:** `python memory/forge/forecast_backtest.py` → **EXIT 0, status PASS** (deterministic: two consecutive runs identical).
Selftest: `python memory/forge/forecast_backtest.py --selftest` → **ALL PASS (3 tests)**.

## What it does (no vibes, just measurements)
- **Part 1 - real track record (pure measurement):** replays all **108** historical next10 snapshots in
  `memory/goals/history/` (**818** p_reached forecasts across **11** lanes), scores each against the project's
  OWN outcome detector (`forecast_calibration.check_outcomes`), writes a live-forecaster Brier curve.
  - Live Brier by day: 11-23=0.1438(n=223) · 11-24=0.1385(n=260) · 11-25=0.3447(n=209) · 11-26=0.3163(n=126).
  - Per-lane measured base-rate + systematic bias (these SEED the A/B world, not invented):
    verifier bias=+0.5244 (severely over), mechanic +0.4226, outlet +0.4148, archivist +0.3908,
    scribe -0.2221 (under), researcher -0.1682, orchestrator -0.1596.
- **Part 2 - A/B feedback backtest (the mechanism under test):** imports the REAL
  `forecast_calibration` module and exercises its residual loop (`weight_adjustment = -calibration_gap`).
  Two arms over **10 cycles**, 8 goals/lane/cycle, top-K=40/80 dispatch budget, seed=20261126:
    - baseline : forecast = raw p_hat (no feedback)
    - feedback : forecast = clamp(p_hat - running_gap), running_gap = cumulative-mean calibration gap
                carried forward each cycle (how real calibration accumulates over history).
  **Result (before/after numbers):**
    - mean Brier      baseline=**0.1948** → feedback=**0.1234**  (Δ **-0.0714**, lower is better)
    - mean top-K prec baseline=**0.1775** → feedback=**0.3175**  (Δ **+0.1400**, higher is better)
    - Brier curves: baseline flat ~0.18-0.21 all 10 cycles; feedback starts 0.1973 (=baseline, no residual yet)
      then converges to 0.09-0.14 as the learned gap tracks each lane's true bias.

## Guard rails (so it can't be rigged to always pass) — `--selftest`
- T1 biased lanes   → feedback Brier 0.314 < baseline 0.4442  (mechanism corrects real bias)
- T2 no-bias lanes  → arms ~equal, Δ=0.0017                    (feedback does NOT hurt when already calibrated)
- T3 real module import + check_outcomes shape OK

## Artifacts
- `memory/forge/forecast_backtest.py` (harness)
- `memory/forge/forecast_backtest_last.json` (machine-readable results)
- `memory/forge/forecast-backtest-report.md` (human report, regenerated each run)
