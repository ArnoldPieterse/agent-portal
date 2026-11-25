# Goal #1: Convergence-Informed Goal Prioritizer - EVIDENCE
Date: 2026-11-25
Status: DONE (verified)

## What was built
`memory/orchestrator/goal_prioritizer.py` — re-ranks next10.json candidates by convergence impact:
  score = p_reached * complexity_factor * lane_urgency / hours
  - complexity_factor modulated by autonomy_score trend (improving → accept harder goals)
  - lane_urgency = 1 - (done/total), so lanes closer to completion get higher priority

## Acceptance test
- Script runs: `python memory/orchestrator/goal_prioritizer.py --top 5` ✓
- Self-test: `memory/orchestrator/test_goal_prioritizer.py` 5/5 PASS ✓
- Output includes fleet % + autonomy score + ranked goals with convergence_score

## Files
- memory/orchestrator/goal_prioritizer.py (main script, ~70 lines)
- memory/orchestrator/test_goal_prioritizer.py (self-test, 5 cases)
