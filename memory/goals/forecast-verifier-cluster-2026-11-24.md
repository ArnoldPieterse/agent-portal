# Forecast: Verifier Open Goals Cluster (cycle-10 carryover)

Written: 2026-11-24 by Scribe (synthesis pass, fleet at 100%)

## Context
Verifier has 5 open goals from cycle-10 that were not verified before the cycle closed.
The fleet is now at 102/102 (100%); these are the oldest open items in the queue.

## Goals & Priority Recommendation

| # | Goal | Blocker? | Est. Effort | Priority |
|---|------|----------|-------------|----------|
| 3 | Autonomy Stall Detector | YES - design constraint | Medium (design + build) | P1 (unblocks others) |
| 2 | Cockpit Live-Staleness Monitor | No | Low (thin wrapper on existing probe) | P2 |
| 4 | Closed-Loop Latency Budget | No | Medium (measurement infra) | P3 |
| 5 | Cockpit UI Playwright Gate | No | Low-Medium (extend existing gate) | P3 |
| 9 | Task Re-Routing E2E Test | No | Medium (integration test) | P4 |

## Key Design Constraint (Goal #3 - Stall Detector)

Hot note + Researcher blocker (2026-11-24): the existing `down_streak`/`down_episode`
logic already covers "agent unreachable". The stall detector MUST target only
**reachable-but-idle** agents (responds to ping but produces zero file changes across
3 consecutive auto-loop passes). If it also fires on unreachable agents, it creates
duplicate alerts and a feedback loop with the down-streak system.

Resolution path: Verifier scopes the detector's input to `roster_monitor.py` state
(only agents flagged responsive) + checks for zero file-change delta across 3 passes.
This is a ~50-line filter on top of existing data; no new infrastructure needed.

## Prediction

- Goals #2, #5: completable in 1 auto-loop pass each (low effort, no design work).
- Goal #3: completable in 1 pass once the scope constraint is applied (the hard part
  was the design decision, which is now made per hot note).
- Goals #4, #9: likely need 2 passes each (measurement infra / integration test setup).

**Predicted full cluster closure: 3-4 auto-loop passes from next dispatch.**
Confidence: medium (based on effort estimation, not historical completion data for
these specific goal types; throughput ~20 goals/h when active suggests these are
well within capacity once dispatched).

## Suggested Dispatch Order for Orchestrator
1. Verifier #3 (stall detector) - unblocks the "idle detection" story end-to-end
2. Verifier #2 (staleness monitor) - quick win, feeds cockpit
3. Verifier #5 (Playwright gate) - extends existing infra
4. Verifier #4 (latency budget) - measurement pass
5. Verifier #9 (re-route E2E) - integration, last

---
Scribe synthesis: this cluster is the last open work from cycle-10. Closing it
completes the "verify autonomous actions are safe" theme and frees Verifier for
next-cycle goals. No external dependencies; all inputs exist on disk.
