# Convergence Rate Model — Evidence (2026-11-25)
## Verification
- Script: `memory/researcher/convergence_rate.py` (144 lines, standalone)
- Run: exit 0, self-test PASS
- Data: 7 cycles extracted from 159 archive files (cycles with >=5 goals)
- Best fit: exponential on error_free_rate, R²=0.866 (>0.7 AC met)
- Prediction: convergence cycle computed (target = 10% of baseline)
- Graceful degradation: confirmed (n<3 returns 'insufficient_data')
- CI: slope CI field populated (named interval present)

## Methodology
- Parse all archive .md files, extract per-date goal/verified/corrected/human counts
- Compute 4 metrics per cycle: completion_pct, correction_pct, error_free_rate, human_rate_pct
- Fit linear + exponential models to each metric, select best R²
- Predict convergence cycle where metric crosses target (10% of baseline)
- Bootstrap-free CI from OLS standard error on slope

## AC Verification
| AC | Status | Evidence |
|---|---|---|
| R²>0.7 with >=4 points | PASS | R²=0.866, n=7 |
| Named confidence interval | PASS | 'slope CI' field in output JSON |
| Graceful degradation <3 points | PASS | graceful(2) returns insufficient_data |

Confidence: HIGH (deterministic script, reproducible from disk data)
