# Failure-Mode Indicator Validation (goal #5) - Cycle-3 P/R Table

Date: 2026-11-18. Data: model-load.jsonl (110 runs, 11-16 15:05 -> 11-18 00:45), wedge-events.jsonl (1 event). Cycle-3 window ~34h.

## Method
For each of the 4 cycle-2 leading indicators, I checked whether it FIRED during cycle-3 and whether that firing corresponded to a TRUE incident (precision) or any incident was MISSED (recall). Data source: model-load.jsonl `missing` field as proxy for "gap/dead-seat"; wedge-events.jsonl for indicator #4. Journal files not accessible in sandbox -> indicator #3 inconclusive.

## P/R Table

| # | Indicator | Fired? | TP | FP | FN | Precision | Recall | Verdict |
|---|-----------|--------|----|----|-----|-----------|--------|----------|
| 1 | Cluster >=2 agents gap >90s same pass | YES (96/110 runs) | 96* | 0 | 0** | 100%* | N/A** | REWORK |
| 2 | Repeated gaps ONE agent >=3 consecutive | YES (6 agents) | 6* | 0 | 0** | 100%* | N/A** | KEEP (rework trigger) |
| 3 | Max-gap magnitude >300s | ? (no journal data) | - | - | - | INCONCLUSIVE | INCONCLUSIVE | HOLD |
| 4 | Journal mtime frozen + run_state busy | YES (1 wedge event 11-16T04:19) | 1 | 0 | 0 | 1/1 (n=1) | N/A** | KEEP |

*All "TPs" for #1 and #2 confirm a STATIC state (models unloaded at cycle start, seats stayed dead). Not predictive of NEW failures.
**No NEW discrete failure transitions occurred in this window, so recall is unmeasurable (no new incidents to predict).

## Key Finding: Static-State vs Transition Problem
Cycle-3's dominant condition is 6/8 agents not_loaded from the START. Indicators #1 and #2 fire on every single run because they detect STATE ("agent X is missing") rather than TRANSITION ("agent X just went from loaded to missing"). In a healthy cycle with all seats up, these would be quiet until something breaks - exactly what we want. In this degraded cycle, they're always-on alarms.

**Design implication for adaptive probe:** The alert logic should fire on DELTA (newly-missing agent joins the set) not LEVEL (agent is currently missing). Concretely:
- Maintain a rolling "known-dead" set per agent.
- Fire indicator #1 when an agent TRANSITIONS into the dead set (not when it's already in it).
- Fire indicator #2 only on the 3rd consecutive miss AFTER the first (i.e., transition + confirmation, not just state).

## Cycle-3 Incident Inventory (for recall measurement)
1. Model-unload at cycle start (11-16 ~15:00): NOT a new incident - expected baseline. Agents: Orchestrator, Researcher (not_loaded); Archivist, Designer (unreachable from start).
2. Wedge event 11-16T04:19: portal unresponsive, recovered=false. Detected by existing wedge detector. [Before formal cycle-3 start but within data window.]
3. Goal-stall loop bug (11-16): operational bug in portal code, not a model/host failure. Not predictable by any of the 4 indicators.

No NEW discrete failures occurred mid-window that should have been predicted. This means the dataset is insufficient to measure recall for any indicator.

## Recommendations for Adaptive Probe

| Indicator | Action | Rationale |
|-----------|--------|----------|
| #1 (cluster) | REWORK: fire on transition, not state | Always-on in degraded fleet; useful only at transition moment |
| #2 (dead-seat) | KEEP + rework trigger to "3rd miss after first" | Correct mechanism; adjust threshold from absolute to relative |
| #3 (gap magnitude) | HOLD - need journal data next cycle | Cannot validate without access to runs/*.journal |
| #4 (wedge) | KEEP as-is | Proven (n=1), critical for host-level failures, zero false positives |

## Confidence
- Indicators #1/#2: HIGH confidence in mechanism validity; LOW confidence in threshold values (single-fleet sample, static-state window).
- Indicator #4: MEDIUM (n=1 true positive, correct detection, but no negative control).
- Overall: This validation confirms the indicators work as STATE DETECTORS. To validate them as EVENT PREDICTORS, we need a cycle where at least one seat transitions from alive->dead mid-window.

## Cross-references
- Original indicator list: memory/researcher/failure-mode-indicators-2026-11-16.md
- Model-load data: memory/ops/model-load.jsonl (110 entries)
- Wedge events: memory/ops/wedge-events.jsonl
- Goal-stall bug (context): memory/portal/bugs/goal-stall-loop-2026-11-16.md
