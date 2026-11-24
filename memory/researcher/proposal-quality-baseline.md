# Proposal Quality Baseline - Findings

**Date:** 2026-11-25
**Goal:** #7 Researcher cycle-17 - "establish baseline quality score for auto-generated goal proposals vs human-refined goals. Measure gap; identify which auto-goals need least refinement. Verified: ≥10 proposals scored; gap quantified; top-3 'best auto-goals' identified."

## Methodology

Scored **626 goals** (328 auto-proposals + 294 human-refined/verified) from cycles 10-16 on 5 dimensions:
1. **Specificity** (file paths, commands, thresholds) - max 5
2. **Verification clarity** (testable criteria present) - max 5  
3. **Scope focus** (single task vs broad) - max 5
4. **Output definition** (specified artifact) - max 5
5. **Actionability** (imperative verbs, clear first step) - max 5

## Results

| Metric | Auto-Proposals | Human-Refined | Gap |
|--------|---------------|---------------|-----|
| Mean score | 47.0% | 50.6% | **+3.6 pp** |
| Range | 20-76% | 24-80% | - |

### Dimension Breakdown (auto-proposals)
| Dimension | Mean/5 | Interpretation |
|-----------|--------|----------------|
| Specificity | 2.12 | Moderate - most reference files/commands |
| Verification | 2.73 | Decent - most have "Verified:" criteria |
| Scope | 4.32 | Good - goals are generally focused |
| Output | 1.62 | **Weak** - most don't specify artifact path clearly |
| Actionability | 0.98 | **Very weak** - few use strong imperative verbs |

### Top-3 Best Auto-Goals (least refinement needed)
1. **Mode Transition Integration Test** (verifier, c15) - 76%
2. **Tiered Summary Ladder** (archivist, c12/c14) - 72%
3. **Fleet Autonomy Score** (orchestrator, c16) - 72%

## Key Findings

1. **Gap is small (+3.6 pp):** Auto-generated proposals are already close to human-refined quality. The orchestrator's goal-drafting is effective.
2. **Weakest dimension: Actionability (0.98/5).** Goals rarely start with clear imperative verbs. Adding "Build X that does Y" framing would improve clarity.
3. **Second weakest: Output definition (1.62/5).** Many goals don't specify the exact output file path. Standardizing "Output: memory/agent/file.ext" would help.
4. **Strong dimension: Scope (4.32/5).** Goals are well-scoped - single focused tasks rather than broad multi-part objectives.

## Verification Criteria Met
- [x] ≥10 proposals scored (328)
- [x] Gap quantified (+3.6 pp)
- [x] Top-3 best auto-goals identified

## Artifacts
- Scoring script + results: `memory/researcher/proposal-quality-baseline.json`
