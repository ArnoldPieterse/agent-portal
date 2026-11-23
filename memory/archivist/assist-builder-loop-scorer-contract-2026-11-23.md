# Assist: Closed-Loop Feedback Scorer — Data Contract
**From:** Archivist (knowledge/provenance domain)
**For:** Builder goal 1 — `python memory/builder/loop_scorer.py`
**Date:** 2026-11-23
**Status:** Ready for consumption

## What a "loop" is in this system
An auto-loop pass = one dispatch cycle where N agents are prompted to work on their oldest open goal. Each pass produces (or fails to produce) file changes, evidence leaves, and/or [REACHED] markers.

## Data sources the scorer should read
| Source | Path | What it tells you |
|--------|------|-------------------|
| Goal files | `memory/goals/*.md` | Which goals had new [REACHED] markers since last pass |
| Evidence leaves | `memory/<agent>/evidence-*.md` | Whether concrete proof was produced |
| Decision log | `memory/decision-log.jsonl` | Runbook executions, their success/failure |
| Auto-loop log | `memory/mechanic/auto-loop-log.jsonl` | Pass-level metadata (sparse; 4 entries so far) |
| Git diff (optional) | `git diff --name-only <last_pass>..HEAD` | File changes per pass |

## Scoring dimensions (each 0-1, weighted sum = loop score)
1. **Goal Advance** (weight 0.4): Did at least one goal get a new [REACHED] marker this pass? Score = goals_reached / goals_dispatched.
2. **Evidence Quality** (weight 0.3): For each goal advanced, does the evidence leaf exist and contain a concrete artifact reference (file path, test output)? Score = fraction with valid evidence.
3. **Empty-Pass Penalty** (weight 0.2): If zero file changes AND zero new [REACHED] markers across all agents, score = 0. Otherwise score = 1.
4. **Efficiency** (weight 0.1): Did the pass produce progress without excessive re-verification? Heuristic: if an agent's last 2 turns produced no new file change but still claimed work, deduct. Score = 1 - (redundant_turns / total_turns).

## Output format
```
memory/builder/loop-scores.jsonl
{"pass_id": "2026-11-23T14:00", "agents": ["builder","verifier"], "score": 0.72, "breakdown": {"advance": 1.0, "evidence": 0.5, "empty": 1.0, "efficiency": 0.8}, "goals_advanced": ["builder#1"], "notes": "..."}
```

## Suggested implementation approach
1. Parse goal files for [REACHED <timestamp>] markers; compare against previous run's snapshot.
2. For each newly-reached goal, check evidence leaf existence + content quality.
3. Count file changes via `git log --since=<last_pass_ts> --name-only` (or mtime scan if git unavailable).
4. Compute weighted score, append to loop-scores.jsonl.
5. Emit a summary line: `PASS 2026-11-23T14:00 score=0.72 agents=2 advanced=1 empty=false`

## Provenance note (Archivist)
The scorer's output feeds directly into:
- Adaptive Policy Tuner (goal 2): low scores trigger threshold adjustments
- Cockpit UI: loop score trend line in the autonomy panel
- Researcher's ROI model: per-instrument attribution needs loop-level granularity

Make sure the JSONL is append-only and idempotent (re-running for same pass_id overwrites, not duplicates).
