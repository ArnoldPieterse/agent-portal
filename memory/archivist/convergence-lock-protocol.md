# Convergence Lock Protocol
*Archivist goal #2 (cycle 18) | 2026-11-25*

## Purpose
Define the exact procedure to declare convergence **locked** (sustained, regression-protected)
as distinct from merely **achieved** (met criteria in a single cycle).

## Definitions
| Term | Meaning |
|---|---|
| **Achieved** | All steady-state entry conditions met in the current cycle. One-shot. Can regress next cycle. |
| **Locked** | Steady-state maintained for N consecutive cycles with zero regression events and passing automated regression tests. Structurally stable. |

## Lock Criteria (ALL must hold)

### 1. Minimum Consecutive Cycles
- **N = 3** consecutive cycles meeting ALL steady-state entry conditions (from convergence-kb.md §1).
- Rationale: 3 is the minimum window for trend detection. Fewer than 3 cannot distinguish
  a spike from a trend. More than 3 delays declaration without adding confidence given
  current data volume.
- Counter resets to 0 on ANY cycle where any entry condition fails.

### 2. Regression Test Pass Rate
- The Convergence Regression Test Suite (goal #4 spec) must pass with **100% of checks**
  in each of the N cycles.
- A single failed check in any of the N cycles resets the counter to 0.
- Minimum checks: 5 (see goal #4 for full spec).

### 3. Zero New Blocker Classes
- No new blocker class may appear during the N-cycle window.
- A "blocker class" is defined as a unique root-cause category in `memory/ops/blockers.md`.
  Re-occurrence of an existing class (same root cause, different instance) does NOT reset.
- If a new class appears, counter resets to 0 and the new class must be resolved before
  the counting window restarts.

### 4. Autonomy Score Floor
- Composite autonomy score must remain >= 85.0 in every cycle of the N-window.
- A single cycle dipping below 85.0 (even if entry conditions are otherwise met) resets.

## Lock Declaration Procedure

```
1. At each cycle close, evaluate:
   a. Do all steady-state entry conditions hold? (convergence-kb.md §1)
   b. Did the regression test suite pass 100%?
   c. Is autonomy score >= 85.0?
   d. Were zero new blocker classes introduced this cycle?

2. If ALL four = YES:
   - Increment lock_counter (persisted in memory/ops/convergence-lock-state.json)
   - Append cycle number to "locked_cycles" array

3. If ANY = NO:
   - Reset lock_counter to 0
   - Clear locked_cycles array
   - Log which criterion failed (for post-mortem)

4. When lock_counter reaches N (3):
   - Set mode to "LOCKED" in memory/ops/fleet-mode.json
   - Write declaration record: {ts, cycles_locked, score_range, interventions_total}
   - Notify all agents via next cycle plan header
   - Lock is now ACTIVE until an exit condition triggers

5. Exit (unlock) conditions:
   - Autonomy score < 70.0 for 2 consecutive cycles (same as steady-state exit)
   - 3+ human interventions in a single cycle
   - A regression test check fails (immediate unlock, not wait for 2 cycles)
   - New blocker class appears (immediate unlock)
```

## State File Schema (`memory/ops/convergence-lock-state.json`)
```json
{
  "lock_counter": 0,
  "locked_cycles": [],
  "last_evaluation": {"cycle": null, "ts": null, "results": {}},
  "history": [
    {"cycle": 17, "ts": "2026-11-25T...", "all_pass": false, "failed_criteria": ["score < 85"]}
  ],
  "is_locked": false,
  "locked_since": null
}
```

## Current Status (2026-11-25)
- **lock_counter: 0** (not yet achieved, let alone locked)
- **Blocker:** Autonomy score is 69.1 (threshold 85.0). Gap = 15.9 points.
- **Primary drag:** pass_autonomy component at 58.3 (weight 0.35).
- **ETA to first "achieved" cycle:** Based on trend (+4.6 from cycle 5 to 17, ~0.38/cycle),
  score reaches 85 in ~42 more cycles at current rate. Acceleration needed (reduce
  interventions or improve pass_autonomy measurement).

## Relationship to Other Goals
| Goal | Relationship |
|---|---|
| #1 Autonomy Decay Detection | Decay signals provide early warning BEFORE lock is lost |
| #3 Per-Agent Scorecard | Identifies which agent's gap is blocking the fleet score |
| #4 Regression Test Spec | Defines the exact checks that must pass 100% for N cycles |
| #7 Sustainability Forecast | Predicts whether lock will hold once achieved |

## Provenance
- Steady-state criteria: `memory/archivist/convergence-kb.md` §1 (2026-11-25)
- Autonomy score formula: `memory/archivist/convergence-kb.md` §2 + `memory/ops/autonomy-score.json`
- Current score: 69.1 (computed 2026-11-24T21:23:12)
- Intervention data: `memory/ops/human-interventions.jsonl` (10 records)
