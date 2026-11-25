# Steady-State Declaration — Fleet Autonomy Convergence

**Status:** NOT YET DECLARED (criteria not fully met as of 2026-11-25)
**Last evaluated:** 2026-11-25 01:28 UTC

## 1. Criteria for Steady-State Entry

All of the following must hold simultaneously for a full cycle (≥24h):

| # | Criterion | Target | Current | Met? |
|---|-----------|--------|---------|------|
| C1 | Fleet goal completion | ≥95% (76/80) | 82.5% (66/80) | ✗ |
| C2 | Human interventions in cycle | 0 | 1 (cycle 17, unblock) | ✗ |
| C3 | Autonomy score | ≥80/100 | 69.1 | ✗ |
| C4 | All lanes at 10/10 with verified evidence | 8/8 lanes | 6/8 (designer 9/10, scribe now 2/10) | ✗ |
| C5 | No regressions vs prior cycle | completion Δ ≥ 0 | C16 regressed vs C15 | ✗ |

**Evidence sources:** `memory/ops/fleet-mode.json`, `memory/ops/autonomy-score.json`, `goal_ledger.json`, `memory/ops/human-interventions.jsonl`

## 2. Behavior Change on Declaration

When all criteria are met and the declaration is activated:
- Fleet mode transitions WORK → **STEADY** (new mode in `fleet_mode.py`)
- Auto-loop dispatch switches from goal-driven to maintenance-only rotation
- Human interventions become exceptional events requiring post-hoc justification log entry
- Cycle duration target tightens from 24h to ≤12h (less work = faster cycles)
- Scribe produces a convergence digest weekly instead of per-cycle

## 3. Exit Conditions (leaving steady-state)

Steady-state is exited if ANY of the following occurs:
- A new fleet-level goal is added (scope expansion) → return to WORK
- Autonomy score drops below 70 for two consecutive cycles → return to WORK + root-cause analysis
- A human intervention of type "redirect" occurs (not unblock/approve) → review scope alignment
- Fleet completion drops below 90% → investigate slippage before resuming

## 4. Declaration Record

| Field | Value |
|-------|-------|
| Declared date | _(pending)_ |
| Declared by | Scribe (auto-generated on criteria satisfaction) |
| Criteria snapshot | See §1 table at time of declaration |
| First steady cycle | _(pending)_ |
| Exit triggered | _(none yet)_ |

---
*This document is a living template. It will be updated in-place when criteria are met. The "Declared date" field and behavior change activation happen atomically via `fleet_mode.py` transition.*
