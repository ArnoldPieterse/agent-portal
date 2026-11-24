# Steady-State Definition — Single Source of Truth (SSOT)
**Lane:** Archivist | **Created:** 2026-11-25 | **Status:** AUTHORITATIVE
**Referenced by:** All agents. When in doubt about steady-state criteria, this document wins.

---

## 1. Definition

Steady-state is the fleet's target operating mode characterized by:
- Autonomous goal completion with minimal human intervention
- Stable cycle cadence (predictable duration)
- Self-sustaining convergence metrics trending toward or at target

It is NOT a terminal state — the fleet operates in steady-state while continuing to improve.

---

## 2. Entry Criteria (ALL must be true simultaneously)

| # | Criterion | Threshold | Measurement Method | Data Source |
|---|-----------|-----------|-------------------|-------------|
| E1 | Goal completion | ≥ 80% of current cycle goals marked `[REACHED]` | `goals_reached / goals_total` from goal_ledger.py | `memory/ops/fleet-mode.json` |
| E2 | Autonomy score | ≥ 85.0 (composite, 0–100 scale) | Formula in §3 below | `memory/ops/autonomy-score.json` |
| E3 | Intervention rate | ≤ 1 human intervention per agent per rolling 7-day window | Count entries in trailing 7d, group by agent | `memory/ops/human-interventions.jsonl` |

**Entry evaluation cadence:** At each cycle close (when goal_ledger.py records the final `[REACHED]` for the last open goal).

**Entry action:** Write `"mode": "STEADY-STATE"` to `memory/ops/fleet-mode.json`. Log transition event.

---

## 3. Autonomy Score Formula (authoritative)

```
autonomy_score = 0.35 × pass_autonomy + 0.25 × duration_score + 0.20 × rework_score + 0.20 × trend_score
```

All components are on a 0–100 scale.

### 3.1 pass_autonomy
- **Definition:** Percentage of agent passes completed without any human intervention.
- **Formula:** `(passes_without_intervention / total_passes) × 100`
- **Source:** Derived from `memory/ops/human-interventions.jsonl` (intervention events) cross-referenced with pass logs.
- **Edge case:** If no passes recorded, component = 50 (neutral).

### 3.2 duration_score
- **Definition:** How close cycle duration is to the 24h target.
- **Formula:** `max(0, 100 − max(0, (actual_hours − 24) / 24 × 100))`
- **Source:** `memory/ops/cycle-durations.jsonl` → latest entry's `duration_hours`.
- **Edge case:** If duration < 24h, score = 100 (bonus for speed).

### 3.3 rework_score
- **Definition:** Inverse of rework rate — measures first-pass quality.
- **Formula:** `(1 − rework_rate) × 100`
- **Source:** `memory/ops/efficiency-index.jsonl` → latest cycle's `rework_rate`.
- **Edge case:** If no efficiency data, component = 50 (neutral).

### 3.4 trend_score
- **Definition:** Direction of autonomy improvement over recent cycles.
- **Formula:** `clamp(50 + (score_current − score_2_cycles_ago) × 1.0, 0, 100)`
- **Source:** Prior `autonomy-score.json` snapshots (need ≥ 3 data points).
- **Edge case:** If < 3 prior scores available, component = 50 (neutral/flat).

### Current State (2026-11-24)
| Component | Value | Weight | Contribution |
|-----------|-------|--------|-------------|
| pass_autonomy | 58.3 | 0.35 | 20.4 |
| duration_score | 80.0 | 0.25 | 20.0 |
| rework_score | 93.6 | 0.20 | 18.7 |
| trend_score | 50.0 | 0.20 | 10.0 |
| **Total** | | | **69.1** |

---

## 4. Exit Criteria (ANY triggers exit from steady-state)

| # | Trigger | Threshold | Detection |
|---|---------|-----------|-----------|
| X1 | Autonomy score decline | < 70.0 for 2 consecutive cycle closes | Compare last 2 autonomy-score.json values |
| X2 | Intervention spike | > 3 total human interventions in single cycle | Count entries in current cycle's date range |
| X3 | Cycle duration anomaly | Duration > rolling mean + 2σ (min 3 data points) | Compute from `memory/ops/cycle-durations.jsonl` |
| X4 | Goal completion stall | < 50% goals reached after 1.5× expected cycle time | Compare elapsed vs. forecast ETA in next10.json |

**Exit action:** Write `"mode": "WORK"` to `memory/ops/fleet-mode.json`. Log transition event with trigger ID.

---

## 5. Expected Behavior in Steady-State

When mode = STEADY-STATE:

| System | Normal (WORK) | Steady-State |
|--------|--------------|--------------|
| Probe cadence | 5 min | 15 min (Mechanic auto-adjuster) |
| Cycle frequency | Daily trigger | Biweekly trigger (Builder scheduler adaptation) |
| Goal generation | Full cycle skeleton | Minimal: maintenance + improvement only |
| Human notification | Per-intervention | Weekly digest only |
| Recovery urgency | Immediate on SLA breach | Escalate only on SLA breach (lighter routine recovery) |
| Dashboard emphasis | Progress toward 100% | Stability metrics (variance, trend) |

### Agent Behavior in Steady-State
- **Orchestrator:** Reduces dispatch frequency; focuses on exception handling.
- **Researcher:** Shifts from goal-finding to pattern analysis + prediction accuracy tracking.
- **Builder:** Maintenance mode; only builds when triggered by degradation signal.
- **Verifier:** Reduced test battery (smoke tests only); full battery on exit trigger.
- **Mechanic:** Extended probe intervals; predictive monitoring replaces reactive.
- **Designer:** No active UI changes unless steady-state indicators need update.
- **Scribe:** Weekly synthesis instead of per-cycle.
- **Archivist:** Convergence trajectory tracking + readiness assessment (weekly).

---

## 6. Measurement Methodology

### Data Collection
1. **Per probe (5/15 min):** Seat health, latency → `seat-matrix.json`
2. **Per pass:** Goal activity, intervention events → `human-interventions.jsonl`
3. **Per cycle close:** Autonomy score recompute, efficiency index, duration log
4. **Per week (steady-state):** Readiness assessment (Archivist goal #10)

### Computation Pipeline
```
Raw data sources
    ↓
memory/ops/cycle-durations.jsonl     (duration_score input)
memory/ops/human-interventions.jsonl (pass_autonomy + E3 input)
memory/ops/efficiency-index.jsonl    (rework_score input)
memory/goals/*.md [REACHED] markers  (E1 input via goal_ledger.py)
    ↓
autonomy-score.json                  (composite score, recomputed at cycle close)
fleet-mode.json                      (mode state, updated on entry/exit)
    ↓
Dashboard / Cockpit display
```

### Validation
- Verifier Goal #1 (Convergence Metric Validation) checks formula correctness against source data.
- Archivist Goal #8 (Convergence Metric Lineage) documents full computation chain for audit.

---

## 7. Transition State Machine

```
                    E1∧E2∧E3 all true
    WORK ──────────────────────────────────► STEADY-STATE
      ▲                                          │
      │         X1∨X2∨X3∨X4 any true            │
      └──────────────────────────────────────────┘
```

- **WORK → STEADY-STATE:** Atomic. All 3 entry criteria evaluated at same cycle close.
- **STEADY-STATE → WORK:** Immediate on any exit trigger. No debounce (fail-safe).
- **No intermediate states.** Binary mode only.

---

## 8. Versioning & Change Control

- Changes to this document require: (a) Archivist update, (b) Verifier validation of new criteria against data, (c) Orchestrator acknowledgment in TODO.md.
- Formula weight changes: log old weights + rationale in change history below.

### Change History
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-11-25 | Initial SSOT created | Cycle 17 convergence topic; formalize criteria scattered across ops files |

---
*This is the authoritative definition. All other references to steady-state criteria should link here rather than restate.*
