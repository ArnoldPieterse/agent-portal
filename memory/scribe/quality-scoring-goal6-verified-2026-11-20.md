# Goal 6 Verification: Synthesis Quality Scoring
Date: 2026-11-20
Agent: Scribe
Status: PASS

## Acceptance Criteria
| Criterion | Result |
|-----------|--------|
| >=10 files scored | PASS (67 files) |
| Vague file scores <40 | PASS (37.7 - 2-week-old unstructured note) |
| Specific decision scores >80 | PASS (82.3 - anti-stall v2 decision with context+next-steps) |
| Endpoint returns valid JSON | PASS (/api/synthesis/quality -> valid JSON, fleet avg=68.8) |

## Artifacts
- memory/scribe/quality_scoring.py - scoring script (clarity/completeness/actionability/recency heuristics)
- agent_portal.py - /api/synthesis/quality endpoint added (function _synthesis_quality_snapshot + route)

## Scoring Weights
- Clarity: 30% (title, structure, sentence length, wall-of-text penalty)
- Completeness: 30% (context markers, decision statements, agent mentions, next steps)
- Actionability: 20% (file paths, commands, action items, checkboxes, agent assignments)
- Recency: 20% (date in filename vs today; <7d=90-100, <30d=50-80, <60d=20-40, >60d=0-20)

## Fleet Averages (2026-11-20)
clarity=81.1 completeness=65.5 actionability=38.3 recency=82.1 overall=68.8