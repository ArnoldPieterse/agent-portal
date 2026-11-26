# Autonomy Progression Model — Fleet (cycle-20)
_Built 2026-11-26T14:21:28Z by Builder as an assist on Archivist goal #1. Owner: **Archivist**. Round topic: Fleet Autonomy Convergence._
## What is verified vs directional
- **Fleet-level progression: VERIFIED.** Fit over 5 real cycle points (12, 15, 16, 17, 18). Selected model = logistic, **R² = 0.7729** (>0.6 AC).
  - Completion% fits — linear R²=0.4412, logistic(saturation) R²=0.7729. The structural c12→c17 jump is captured by the saturation model, not a straight line.
  - Interventions/cycle — linear R²=0.7547 (flat ~1-3/cycle; agents are not escalating).
  - Fleet steady-state (85% completion) crossing placed ≈ cycle 15.9, i.e. **already crossed by c18** (consistent with the observed plateau at ~86% in the latest cycles).
- **Per-agent: DIRECTIONAL (not verified).** Single maturity-scorecard snapshot; no per-agent multi-cycle series on disk yet, so no per-agent R² is claimed and ETAs are directional ranges.
## Per-agent autonomy ranking
| rank | agent | composite | convergence_trend | trend | interventions | gap→100 | directional ETA |
|---|---|---|---|---|---|---|---|
| 1 | builder | 77.8 | 64.23 | stable | 3 | 22.2 | not trending to full autonomy yet |
| 2 | scribe | 73.2 | 75.06 | trending_up | 0 | 26.8 | not trending to full autonomy yet |
| 3 | verifier | 72.6 | 76.59 | trending_up | 1 | 27.4 | not trending to full autonomy yet |
| 4 | designer | 72.2 | 70.47 | trending_up | 1 | 27.8 | not trending to full autonomy yet |
| 5 | orchestrator | 71.6 | 72.39 | trending_up | 2 | 28.4 | not trending to full autonomy yet |
| 6 | mechanic | 66.9 | 65.12 | stable | 2 | 33.1 | not trending to full autonomy yet |
| 7 | archivist | 63.8 | 80.03 | trending_up | 0 | 36.2 | not trending to full autonomy yet |
| 8 | researcher | 53.2 | 84.24 | trending_up | 1 | 46.8 | not trending to full autonomy yet |
## Next step to make per-agent predictions verifiable
Capture the maturity scorecard as a dated snapshot each cycle (drop into `memory/archivist/snapshots/autonomy-scorecard-c<N>.json`). After >=3 snapshots this script can fit a real per-agent series and promote per-agent ETAs from directional to verified.
