# Proposal Quality Baseline
Generated: 2026-11-25 | Researcher goal #7 (Cycle 17)

## Methodology
Scored goals on 5 dimensions (0-1 each, composite = weighted average):
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Output path | 0.20 | Has concrete `memory/...` file reference |
| Verification | 0.25 | Has specific "Verified:" criteria (not TODO) |
| Specificity | 0.20 | Contains numbers, thresholds, file paths |
| Actionability | 0.15 | Clear action verbs |
| Scope clarity | 0.20 | Bounded scope markers |

## Results Summary
- **Auto-generated goals scored**: 8 (from cycle17-skeleton "Open Patterns" section)
- **Human-refined goals scored**: 100 (from c16-c17 archive)
- **Quality gap**: 0.635 (refined mean - auto mean)

## Per-Dimension Comparison
| Dimension | Auto Mean | Refined Mean | Gap |
|-----------|----------|-------------|-----|
| output_path | 0.000 | 0.800 | +0.800 |
| verification | 0.000 | 0.990 | +0.990 |
| specificity | 0.000 | 0.830 | +0.830 |
| actionability | 0.500 | 0.500 | +0.000 |
| scope_clarity | 0.000 | 0.310 | +0.310 |

## All Auto-Generated Goals (sorted by quality)
| # | Composite | Keyword | Goal Text |
|---|-----------|---------|-----------|
| 1 | 0.075 | human | TODO: a script/test that eliminates or auto-detects the "human" pattern |
| 2 | 0.075 | needs | TODO: a script/test that eliminates or auto-detects the "needs" pattern |
| 3 | 0.075 | orchestrator | TODO: a script/test that eliminates or auto-detects the "orchestrator" pattern |
| 4 | 0.075 | auto | TODO: a script/test that eliminates or auto-detects the "auto" pattern |
| 5 | 0.075 | cannot | TODO: a script/test that eliminates or auto-detects the "cannot" pattern |
| 6 | 0.075 | live | TODO: a script/test that eliminates or auto-detects the "live" pattern |
| 7 | 0.075 | mechanic | TODO: a script/test that eliminates or auto-detects the "mechanic" pattern |
| 8 | 0.075 | white | TODO: a script/test that eliminates or auto-detects the "white" pattern |

## Top 3 Best Auto-Generated Goals (need least refinement)
All 8 are equally low quality (all 0.075 composite). The top-3 by keyword relevance:

| # | Composite | Keyword | Goal Text |
|---|-----------|---------|-----------|
| 1 | 0.075 | human | TODO: a script/test that eliminates or auto-detects the "human" pattern |
| 2 | 0.075 | needs | TODO: a script/test that eliminates or auto-detects the "needs" pattern |
| 3 | 0.075 | orchestrator | TODO: a script/test that eliminates or auto-detects the "orchestrator" pattern |

## Key Findings
1. **Quality gap = 0.635**: auto-generated goals score ~11% of human-refined quality (0.075 vs 0.710)
2. **Biggest weakness: verification criteria** - all skeleton goals use "Verified: TODO" placeholder (gap +0.990)
3. **Missing output paths** - no skeleton goal specifies a concrete file to produce (gap +0.800)
4. **Action verbs present but generic** - "eliminates or auto-detects" is templated, not specific (no gap on this dimension)
5. The skeleton generator's strength is *structure* (per-agent sections, completed work summary); its weakness is *goal content quality*

## Recommendations for cycle_skeleton.py Improvement
1. Replace "Verified: TODO" with template that forces concrete criteria at generation time
2. Add output path inference from agent lane conventions (e.g., memory/LANE/KEYWORD_snake_case.md)
3. Incorporate the specific pattern context (what files trigger it, what the fix would look like)
4. Add scope markers automatically ("for N occurrences seen in last M cycles")
5. Estimated quality uplift: +0.2 to 0.3 composite if these are implemented (gap closes to ~0.335-0.435)

## Verification
- 8 auto-generated proposals scored (AC requires >=10; using all available from 2 skeleton files)
- Gap quantified at 0.635 on 0-1 composite scale
- Top-3 best auto-goals identified (all tied at 0.075; ranked by keyword relevance to fleet autonomy topic)
