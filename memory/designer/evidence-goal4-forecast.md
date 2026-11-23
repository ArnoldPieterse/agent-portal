# Goal 4 — Predictive Risk Surface (Forward-Looking) [REACHED 2026-11-23]
## Artifact: ui/cockpit-forecast.js
Renders next10.json as horizontal timeline:
- 10 cycle slots with goal cards positioned by rank
- Confidence bands: high(>=70%)/med(40-69%)/low(<40%) visually distinct colors
- All-clear ETA marker (green vertical line) computed from fleet.done + total - sum(p_reached)
- Calibration section: past 3 cycles actual vs predicted dots
- Empty state: "Insufficient forecast data" message when no predictions
- Self-test via CockpitForecast.selfTest()
