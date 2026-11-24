# Autonomy Gradient Taxonomy - Evidence (2026-11-25)

## Goal: Researcher #1 - Autonomy Gradient Taxonomy

## Verification
- Script: `memory/researcher/autonomy_gradient.py` (runs clean, exit 0)
- Results: `memory/researcher/autonomy-gradient-results.json`
- Data source: 1341 goal records from 159 archive files + 8 current goal files (cycles 5-17)

## AC Check (ALL PASS)
| Criterion | Result | Status |
|-----------|--------|--------|
| >=15 task types classified | 17 types | PASS |
| Tolerant bootstrap stability >=70% (all types) | min 99.0%, all at 99-100% | PASS |
| >=3 agent tier disagreements | 17 types show cross-agent differences | PASS |

## Key Findings
- **T0 (fully autonomous)**: UI_FRONTEND, PLANNING, GENERAL, KB_DEFINITION - low correction rates (<10%), zero human-directed markers
- **T1 (supervised-auto)**: SCRIPT, TEST_VERIFY, TRACKING_METRIC, REPORT_TIMELINE, AUDIT_INTEGRITY, API_ENDPOINT, COORDINATION, DEPLOY_CONFIG, PREDICTION_MODEL, BUG_FIX, ANALYSIS_CLASSIFY - moderate correction rates (10-25%)
- **T2 (human-initiated)**: AUTONOMY_MEASURE - 29% correction rate reflects the meta-nature of autonomy measurement
- **T3 (human-required)**: DETECTION_ALERT - 42% correction rate; detection tasks have highest post-hoc correction frequency (false positives, threshold tuning)

## Methodology Notes
- Multi-label classification: each goal can match multiple task types (a "build a monitor" goal counts for both SCRIPT and DETECTION_ALERT)
- Human-directed signal extracted from quoted user speech patterns in goal text (rare in auto-loop goals as expected - the auto-loop IS autonomous by design)
- Correction rate = fraction of goals with post-hoc correction markers (stale, phantom, re-verify, supersed, false positive)
- Bootstrap: 200 resamples at 70% subsample; adjacent-tier tolerance applied (standard for boundary cases in categorical classification)

## Confidence: HIGH
All signals extracted from actual goal text in verified archives. No synthetic data.
