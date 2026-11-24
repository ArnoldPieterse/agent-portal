# Convergence Metric Lineage
**Lane:** Archivist | **Created:** 2026-11-25 | **Purpose:** Full computation chain for each dashboard metric. Enables debugging and audit.

For each metric: raw source → transforms → final value. If a number looks wrong, trace it here.

---

## 1. Autonomy Score (composite)

**Final artifact:** `memory/ops/autonomy-score.json` → field `score`
**Current value:** 69.1
**Computed at:** 2026-11-24T15:32:37

### Lineage
```
┌─────────────────────────────────────────────────────────────────────────┐
│ RAW SOURCES                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  human-interventions.jsonl          cycle-durations.jsonl               │
│  (10 events, cycles 2-17)          (4 entries: C5,C8,C14,C15)           │
│         │                                    │                          │
│         ▼                                    ▼                          │
│  ┌──────────────┐                   ┌──────────────────┐                │
│  │ pass_autonomy│                   │ duration_score   │                │
│  │ = 58.3       │                   │ = 80.0           │                │
│  └──────┬───────┘                   └────────┬─────────┘                │
│         │                                    │                          │
│  efficiency-index.jsonl          prior autonomy-score.json snapshots    │
│  (rework_rate=0.064)             (insufficient → neutral 50)            │
│         │                                    │                          │
│         ▼                                    ▼                          │
│  ┌──────────────┐                   ┌──────────────────┐                │
│  │ rework_score │                   │ trend_score      │                │
│  │ = 93.6       │                   │ = 50.0           │                │
│  └──────┬───────┘                   └────────┬─────────┘                │
│         │                                    │                          │
└─────────┼────────────────────────────────────┼──────────────────────────┘
          │                                    │
          ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM: weighted sum                                                 │
│   score = 0.35×58.3 + 0.25×80.0 + 0.20×93.6 + 0.20×50.0               │
│         = 20.41 + 20.00 + 18.72 + 10.00                                │
│         = 69.13 → rounded to 69.1                                      │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FINAL: autonomy-score.json {"score": 69.1, ...}                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Per-Component Detail

#### pass_autonomy = 58.3
| Step | Operation | Input | Output |
|------|-----------|-------|--------|
| 1 | Count total intervention events | human-interventions.jsonl (all lines) | 10 events |
| 2 | Determine total passes in period | scheduler-log.jsonl / pass records | ~24 passes (inferred) |
| 3 | Compute: (passes - interventions) / passes × 100 | 24 passes, 10 interventions | 58.3 |

**Known issue:** Pass count is inferred, not directly logged. Source of uncertainty.

#### duration_score = 80.0
| Step | Operation | Input | Output |
|------|-----------|-------|--------|
| 1 | Get latest cycle duration | cycle-durations.jsonl last line (C15: 24h) | 24.0 hours |
| 2 | Apply formula: max(0, 100 − max(0, (24−24)/24×100)) | actual=24, target=24 | 100.0 |

**Discrepancy:** Formula gives 100 for exactly 24h, but stored value is 80.0. Possible explanation: uses mean of all 4 durations (24+72+24+24)/4 = 36h → 100 − (36−24)/24×100 = 50... still doesn't match. **FLAG: Unresolved discrepancy — needs Verifier investigation.**

#### rework_score = 93.6
| Step | Operation | Input | Output |
|------|-----------|-------|--------|
| 1 | Get latest rework_rate | efficiency-index.jsonl C15 line | 0.064 |
| 2 | Apply: (1 − 0.064) × 100 | 0.064 | 93.6 |

**Clean lineage.** No issues.

#### trend_score = 50.0
| Step | Operation | Input | Output |
|------|-----------|-------|--------|
| 1 | Check for ≥3 prior score snapshots | autonomy-score.json history | Insufficient (only current) |
| 2 | Apply neutral default | — | 50.0 |

**Expected behavior** until 3+ cycles of data accumulate.

---

## 2. Efficiency Index

**Final artifact:** `memory/ops/efficiency-index.jsonl` → field `efficiency_index`
**Current value (C15):** 0.1833

### Lineage
```
cycle-efficiency.json (C15)         autonomy-score.json        cycle-efficiency-15.json
├── goals_completed: 28             └── rework_rate: 0.064     └── idle_fraction: 0.007
├── passes_used: 142                                                        │
│                                                                           │
▼                                                                           ▼
velocity = 28/142 = 0.1972                                          idle = 0.007
│                                                                           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
                    efficiency_index = velocity × (1−rework) × (1−idle)
                                     = 0.1972 × 0.936 × 0.993
                                     = 0.1833
```

### Per-Factor Detail
| Factor | Value | Source File | Field | Notes |
|--------|-------|-------------|-------|-------|
| goals_completed | 28 | cycle-efficiency.json | goals_completed | Sum of per-agent: 1+9+7+5+6=28 ✓ |
| passes_used | 142 | cycle-efficiency.json | passes_used | Budget was 200; 71% utilization |
| rework_rate | 0.064 | autonomy-score.json | (derived) | Was 0.078, corrected to 0.064 per Builder fix |
| idle_fraction | 0.007 | cycle-efficiency-15.json | idle_fraction | 1 idle pass out of 142 |

**Known issue:** `rework_rate` was stale (0.078) in efficiency-index.jsonl until Builder corrected it to match autonomy-score.json (0.064). The efficiency_index value of 0.1833 uses the corrected rate.

---

## 3. Fleet Mode / Goal Completion %

**Final artifact:** `memory/ops/fleet-mode.json` → fields `mode`, `goal_pct`
**Current values:** mode=WORK, goal_pct=27.5%

### Lineage
```
goal_ledger.py [REACHED] markers in memory/goals/*.md
         │
         ▼
    goals_reached = 22 (counted across all agent goal files)
    goals_total   = 80 (sum of all numbered goals in active files)
         │
         ▼
    goal_pct = 22/80 × 100 = 27.5%
         │
         ▼
    mode determination:
      if goal_pct >= 80 AND autonomy >= 85 AND interventions <= threshold
        → STEADY-STATE
      else
        → WORK (current)
```

### Data Sources
| Field | Source | Method |
|-------|--------|--------|
| goals_reached | memory/goals/*.md | Count `[REACHED` markers |
| goals_total | memory/goals/*.md | Count numbered goal lines `^\d+\.` |
| elapsed_since_activity_h | memory/ops/scheduler-log.jsonl | Time since last entry |
| mode | Computed | Threshold logic (see steady-state-ssot.md §2) |

---

## 4. Throughput (Goals/Hour)

**Final artifact:** `memory/goals/next10.json` → field `throughput_goals_per_hour`
**Current value:** 20.04

### Lineage
```
goals_reached (22) / elapsed_active_hours (~1.1h since cycle start)
         │
         ▼
    throughput = 22 / 1.1 ≈ 20.04 goals/hr
```

**Caveat:** This is instantaneous rate, not sustained. Will decrease as remaining goals are harder. The forecast engine uses this for ETA calculation but applies decay factors.

---

## 5. Cycle Duration (per cycle)

**Final artifact:** `memory/ops/cycle-durations.jsonl` → field `duration_hours`
**Current entries:** C5=24h, C8=72h, C14=24h, C15=24h

### Lineage
```
Archive file dates (start_date, end_date)
         │
         ▼
    duration_hours = (end_date − start_date) in hours
         │
         ▼
    Logged to cycle-durations.jsonl at cycle close
```

**Known gap:** Only 4 entries. Cycles 2,3,7,9,10,12,13,16 have no duration data. Mechanic Goal #3 (Cycle Duration Ops Tracker) will add automated logging.

---

## 6. Intervention Rate

**Final artifact:** Derived from `memory/ops/human-interventions.jsonl`
**Current state:** 10 total events across cycles 2-17

### Lineage
```
Human messages in group chat matching intervention patterns
         │
         ▼ (logged by Intervention Logger Hook - Builder Goal #4)
human-interventions.jsonl entries:
  {ts, cycle, agent, type, context}
         │
         ▼
Per-cycle count: C2=1, C3=1, C5=1, C8=1, C12=1, C14=1, C15=1, C16=2, C17=1
Per-agent count: (see Scribe Goal #6 Intervention Knowledge Graph for full breakdown)
```

**Types observed:** redirect (3), unblock (3), approve (3), + 1 other.

---

## Cross-Metric Dependencies

```
autonomy-score.json ──rework_rate──► efficiency-index.jsonl
       │                                    │
       │ (score feeds fleet-mode)           │ (efficiency feeds dashboard)
       ▼                                    ▼
fleet-mode.json ◄──goals_reached── goal_ledger.py [REACHED] markers
       │
       ▼ (mode determines scheduler behavior)
scheduler cadence (5min WORK / 15min STEADY-STATE)
```

**Audit note:** If autonomy-score.json changes, check that efficiency-index.jsonl rework_rate is consistent (they should reference the same underlying data). The 2026-11-24 stale rework_rate incident (0.078 vs 0.064) showed this can drift.

---

## Discrepancy Log

| Date | Metric | Issue | Status |
|------|--------|-------|--------|
| 2026-11-24 | rework_rate | efficiency-index.jsonl had 0.078, autonomy-score.json implied 0.064 | FIXED by Builder (corrected to 0.064) |
| 2026-11-25 | duration_score | Formula gives 100 for 24h target but stored value is 80.0 | OPEN — needs Verifier investigation |
| 2026-11-25 | pass_autonomy | Pass count (denominator) not directly logged; inferred | OPEN — needs explicit pass logging |

---
*Update this document when any metric formula changes or new data sources are added. The discrepancy log is the primary audit trail.*
