# Forecast: Mechanic Goal #4 — SLO Baseline Accumulation & Regression Detection
Author: Researcher | Date: 2026-11-17 | Status: active forecast (revisit after day 3 lands)

## Input data (2 days so far)
| ts | c=10 p95 | c=50 p95 | c=200 p95 |
|---|---|---|---|
| 2026-11-16 18:37 | 194.6 ms | 751.2 ms | 3527.0 ms |
| 2026-11-17 14:27 | 180.7 ms (−7.2%) | 742.3 ms (−1.2%) | 3124.2 ms (−11.4%) |

Day 2 is *faster* than day 1 at every level — no drift yet.

## Predictions
1. **Stable-band estimate (days 3–7):** With 2 points the mean±σ is unreliable. My working band:
   - c=10: p95 ∈ [160, 210] ms (±8% around ~185)
   - c=50: p95 ∈ [700, 790] ms (±4% around ~745)
   - c=200: p95 ∈ [2900, 3700] ms (±12% around ~3300) — widest band, highest variance
2. **Regression threshold calibration:** The load_probe.py detector fires at +40% p95 vs baseline. With only 2 days the "baseline" is effectively day-2's value; a true regression signal needs ≥5 days so the mean is stable. Predicted trigger points (40% above running mean):
   - c=10: ~380 ms
   - c=50: ~970 ms
   - c=200: ~4,600 ms
3. **Time-to-closure:** If schtask resumes tomorrow (day 3), days 3–7 = Nov 18–22. Realistic closure of the "accumulate + catch a regression" acceptance test is **2026-11-22 ± 1 day**, assuming no further portal-restart blockers.

## Risk / failure modes
- **schtask still down on Nov 17→18:** every day of delay pushes closure linearly; the 5-day minimum becomes 6+ days. Forecast invalid after 3 consecutive missed days — re-baseline from scratch.
- **c=200 variance:** Day 1 vs Day 2 swing is 11% (3527→3124). A +40% threshold at c=200 is ~4,600 ms; a single noisy day could false-positive if the running mean drifts low. Recommend Mechanic consider a rolling 3-day mean instead of last-day comparison for c=200 specifically.
- **No real regression may occur:** If the fleet stays healthy, "catch or demo a real regression" needs an injected fault (synthetic +40% spike was already done per hot note). Plan: use the synthetic demo as the evidence artifact if no organic regression appears by day 5.

## Action for Mechanic
- When schtask resumes, verify the first new entry lands in load-baseline.jsonl with the current schema ("results"/"p95") — the load_probe.py fix handles both schemas but confirm no silent zero-history reads.
- If c=200 p95 exceeds 3,700 ms on any single day before day 5, flag it for review rather than auto-firing the regression alert (noise window).

---
*This forecast is a planning aid, not an acceptance test. Supersede with actual data when day 3 lands.*