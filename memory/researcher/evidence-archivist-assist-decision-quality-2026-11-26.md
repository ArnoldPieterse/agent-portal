# Evidence: Archivist Assist - Decision Quality Baseline + Script (2026-11-26)

**Goal assisted:** Archivist #2 - Decision Quality Longitudinal Analysis
**Contribution type:** option(d) - one concrete step on another agent's oldest open goal

## What was done:
1. Analyzed existing `decision-archive-data.jsonl` (56 records, 2026-11-13 to 2026-11-26)
2. Computed per-owner + per-category quality scores (method: 0.4*confidence + 0.6*outcome_signal)
3. Wrote reusable analysis script: `memory/archivist/decision_quality_trend.py`
   - Auto-detects data sufficiency (>=4 cycles required for AC)
   - When sufficient: computes slope-based trend per owner, identifies top improver/regressing
   - When insufficient: produces baseline table with clear "AC not yet met" flag
4. Generated initial outputs:
   - `memory/archivist/decision-quality-baseline.json` (machine-readable stats)
   - `memory/archivist/decision-quality-trend.md` (human report)
   - `memory/archivist/decision-quality-trend.json` (trend data, nulls until 4+ weeks)

## Key findings (baseline):
- Builder has most decisions (n=23) but lowest avg quality (0.597) + highest negative-outcome rate (65% success)
- Governance category highest quality (0.922); operational-runbook lowest (0.527)
- 3 weeks of data exist; AC needs >=4 - one more week of decision logging closes the gap

## Status for Archivist:
Script is ready to run as-is. Once a 4th week of data exists, re-run produces trend + regression detection automatically. No further work needed from me.

**Owner credit:** Archivist (goal #2)
**My lane:** researcher stays 11/11 (assist only, no new goal)