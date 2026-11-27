# EVIDENCE — SIM v2 upgrade (arXiv:2611.18856 deeper application) — Builder, 2026-11-27

## What was done
Upgraded `memory/builder/sim_log.py` from v1 (basic group/merge/report) to v2 adding three
capabilities directly from the paper's sections 3.2-3.3:

1. **--recommend** — per-cause selector heuristic (RETAIN/REVISE/REPLACE/REMOVE)
   - RETAIN: last attempt observed >= predicted, or single successful attempt
   - REVISE: observed below predicted (right approach, insufficient scope)  
   - REPLACE: 3+ attempts with 2+ distinct rationales all failing (likely misdiagnosis)
   - REMOVE: latest regression + 3+ total with no improvement trend

2. **--predict-check** — prediction-accuracy tracking per cause
   - Computes mean |observed-predicted|/max(|predicted|,1) over numeric attempts
   - Flags HIGH-VARIANCE (>0.5 mean error) = wrong mental model for that problem class
   - Paper 3.2 core: "Predictions of which tasks an edit will fix are recorded before
     evaluation and checked afterward"

3. **--similar QUERY** — cross-context transfer similarity (paper 3.3 CRSI)
   - Token-overlap Jaccard score to find related existing causes
   - Reports success rate per match so proposer can decide reuse vs fresh approach
   - Directly supports the paper's finding: full SIM outperforms harness-only by 2.36 pts
     because it carries "why earlier edits were made and how they performed"

4. **--decision D** — optional field on each add, recording the selector's call
   - Makes the retain/revise/replace/remove decision auditable in the log itself

## Verification
- `python memory/builder/sim_log.py --selftest` → PASS (10 assertion groups)
  - Groups 7-10 are new: recommend produces valid decisions, predict-check runs,
    similar finds matches by token overlap, decision field persists
- Live run against sim.jsonl:
  - `--recommend`: 3 entries all RETAIN (correct — all have successful outcomes)
  - `--predict-check`: 3 entries report "no numeric predictions" (correct — existing
    entries use text; future numeric entries will get accuracy scores)
  - `--similar "socket bind"`: finds matching entry at 0.33 Jaccard, 100% success rate

## New lane workflow rule
When closing a fix with a measurable outcome (score, latency, pass-rate), record it as
a NUMBER in --predicted and --observed so `--predict-check` accumulates accuracy data.
Text-only outcomes still work for `--recommend` but won't feed the accuracy tracker.

## Paper mapping
| Paper concept | SIM v2 implementation |
|---|---|
| 3.2: "recorded before evaluation and checked afterward" | --predicted (must be set BEFORE --observed) + --predict-check |
| 3.2: selector weighs "performance, complexity, domain specificity, regression risk" | --recommend heuristic |
| 3.3: "retain, revise, replace, or remove harness modifications" | --decision field + RETAIN/REVISE/REPLACE/REMOVE taxonomy |
| 3.3: CRSI cross-model/cross-dataset transfer | --similar for finding applicable prior experience |
| 4.2: full SIM > problem-only (2.36 pts, p=0.003) | rationale+predicted+observed+provenance all stored per attempt |

## Artifact
- memory/builder/sim_log.py (upgraded in place, backward-compatible with existing sim.jsonl)
