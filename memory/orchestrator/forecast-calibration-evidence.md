# Dispatch-Forecast Calibration Loop - Evidence

Date: 2026-11-26
Script: memory/orchestrator/forecast_calibration.py

## Self-test results (4/4 PASS)
- T1: known-bad forecaster (predicts 0.9, hits 0%) flagged as over-forecasting; Brier elevated
- T2: perfect forecaster (predictions match outcomes exactly) -> Brier~0, no flags
- T3: miscalibrated lane gets negative weight adjustment for dispatch feedback
- T4: empty predictions -> graceful 'no_predictions' status

## Real run baseline
Brier score: **0.203** (better than random 0.25)
Predictions: 10, Reached: 3 (cycle still in progress)

Per-lane calibration gaps:
- mechanic: gap=+0.76 (worst over-forecaster; predicted 76%, hit 0%)
- verifier: gap=+0.52 (over-forecasting)
- forge: gap=+0.46 (over-forecasting)
- scribe: gap=-0.54 (under-forecasting; predicted 46%, hit 100%)
- builder: gap=-0.48 (under-forecasting; predicted 52%, hit 100%)
- orchestrator: gap=-0.36 (under-forecasting; predicted 64%, hit 100%)

## Key finding
The forecast engine systematically over-estimates difficulty for infra-heavy lanes (mechanic, verifier) and under-estimates for knowledge/synthesis lanes (scribe, builder, orchestrator). The weight_adjustment feedback will correct this in the next dispatch cycle. As more cycles accumulate, Brier should converge toward 0 if the model is well-calibrated.

## Design notes
- Brier score = mean((predicted - actual)^2); range [0,1], lower is better
- Calibration gap = avg_predicted - actual_hit_rate; positive = over-forecasting
- Weight adjustment = -calibration_gap (negative for over-forecasters -> reduce their dispatch priority)
- Outcome detection: keyword overlap between predicted goal title and verified lines in lane goals file
