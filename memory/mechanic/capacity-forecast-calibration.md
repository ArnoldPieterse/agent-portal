# Fleet Capacity Forecast Calibration - 2026-11-26

**Data**: 6 cycles (19-24) of predicted vs actual capacity.

| Cycle | Actual (seats/VRAM/dur) | Predicted (seats/VRAM/dur) |
|-------|-------------------------|---------------------------|
| 19 | 4/12.6GB/27.0m | 3/11.0GB/34.7m |
| 20 | 4/16.7GB/25.6m | 5/18.0GB/37.0m |
| 21 | 4/10.4GB/29.4m | 5/8.9GB/41.5m |
| 22 | 4/17.9GB/32.2m | 4/16.0GB/33.8m |
| 23 | 4/9.0GB/29.3m | 5/9.7GB/29.0m |
| 24 | 4/8.5GB/26.2m | 4/7.7GB/30.0m |

## Results
- **MAE before calibration**: 24.9% (cycles 19-21)
- **MAE after calibration**: 8.1% (cycles 22-24)
- **Improvement**: 67.3% error reduction
- **Pass criterion**: MAE < 20% AND improvement >= 50% -> **PASS**

## Parameter Corrections Applied
- seat_prediction_bias: -0.3 (was overpredicting)
- vram_scale_factor: 1.08 (was underpredicting VRAM headroom)
- duration_scale_factor: 0.92 (was overpredicting cycle duration)

## Artifacts
- memory/mechanic/capacity-forecast-calibration.json
