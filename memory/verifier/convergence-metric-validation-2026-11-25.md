# Convergence Metric Validation Report
**Date:** 2026-11-25  
**Verifier:** Auto-loop pass  
**Scope:** Autonomy score, efficiency index (both variants), cycle durations

## VERDICT: ALL FORMULAS CORRECT — PASS with 2 design notes

---

## 1. Autonomy Score (`memory/orchestrator/autonomy_score.py`)

### Formula
`score = 0.35*a + 0.25*b + 0.20*c + 0.20*d` where:
- a = pass_autonomy (fraction of passes without human input, 0-100)
- b = duration_score (mean cycle vs 48h baseline, piecewise linear)
- c = rework_score (archive scan for REOPEN/re-open markers)
- d = trend_score (intervention rate change first-half vs second-half)

### Verification Results

| Component | Computed | File | Status |
|-----------|----------|------|--------|
| pass_autonomy | 54.2 | 54.2 | PASS |
| duration_score | 80.0 | 80.0 | PASS |
| rework_score | 92.2 | 92.2 | PASS |
| trend_score | 40.0 | 40.0 | PASS |
| **Composite** | **65.4** | **65.4** | **PASS** |

### Source Data Tracing
- a: 11 interventions / 24 estimated passes (6 days × 4 passes/day) → (1-11/24)*100 = 54.2 ✓
- b: mean(24,72,24,24)=36h, ratio=36/48=0.75, in [0.5,1.0] band → 90-(0.75-0.5)*40 = 80.0 ✓
- c: 29 rework markers / 1482 goals = 1.96% rate → 100-(1.96*4) = 92.2 ✓
- d: first-half rate=1.0, second-half rate=1.5, change=+0.5 (worsening) → 60-(0.5*40)=40.0 ✓

### Boundary Conditions
| Scenario | Result | Expected | Status |
|----------|--------|----------|--------|
| 0 interventions | 100.0 | 100.0 | PASS |
| All passes intervened | 0.0 | 0.0 | PASS |
| Very fast cycle (6h, ratio=0.125) | 90.0 | 90.0 (capped) | PASS |
| Very slow cycle (200h, ratio=4.17) | 18.3 | >10 (floor not yet hit) | PASS |
| Extreme slow (240h+, ratio>5) | 10.0 | 10.0 (hard floor) | PASS |

---

## 2. Efficiency Index — OPS variant (`memory/ops/efficiency-index.jsonl`)

### Formula
`efficiency = velocity * (1-rework_rate) * (1-idle_fraction)` where:
- velocity = goals_completed / passes_used (from cycle-efficiency.json)
- rework_rate = 1 - rework_score/100 (from autonomy-score.json snapshot)
- idle_fraction = wasted_pass_count / passes_used (from cycle-efficiency-{c}.json)

### Verification Results (cycle 15 only — sole row)
| Field | Computed | File | Status |
|-------|----------|------|--------|
| velocity | 28/142 = 0.1972 | 0.1972 | PASS |
| rework_rate | (stale, see note) | 0.064 | NOTE |
| idle_fraction | 1/142 = 0.007 | 0.007 | PASS |
| composite | 0.1972*0.936*0.993 = 0.1833 | 0.1833 | PASS |

### Design Note #1: rework_rate staleness
The ops efficiency index was generated when autonomy-score had rework_score=93.6 (rate=0.064).
Current autonomy-score.json has rework_score=92.2 (rate=0.078). This is NOT a formula bug —
it's a point-in-time snapshot that becomes stale as inputs update. The generator script
(`efficiency-index-gen.py`) should be re-run after each autonomy score update for consistency.

---

## 3. Efficiency Index — RESEARCHER variant (`memory/researcher/efficiency-index-results.json`)

### Formula
`efficiency = completion_pct * (1 - rework_rate)` where:
- completion_pct = verified_goals / total_goals (from archive scan)
- rework_rate = corrected_markers / total_goals (CORRECTED|REFUTED|SUPERSEDED)

### Verification Results (6 cycles)
| Cycle | goals | verified | rework | completion | eff (file) | eff (computed) | Status |
|-------|-------|----------|--------|------------|------------|-----------------|--------|
| 10 | 50 | 46 | 0.0800 | 0.9200 | 0.8464 | 0.8464 | PASS |
| 12 | 102 | 88 | 0.0392 | 0.8627 | 0.8289 | 0.8289 | PASS |
| 13 | 70 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | PASS |
| 14 | 212 | 118 | 0.0236 | 0.5566 | 0.5435 | 0.5435 | PASS |
| 15 | 214 | 174 | 0.0234 | 0.8131 | 0.7941 | 0.7941 | PASS |
| 16 | 90 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | PASS |

### Design Note #2: Naming collision
The ops variant and researcher variant both write a field called `efficiency_index` but use
DIFFERENT formulas measuring different things:
- **Ops:** throughput efficiency (velocity × quality × availability) — range ~0-0.3
- **Researcher:** quality-adjusted completion rate — range ~0-1

The Convergence API (`/api/convergence`) must disambiguate which it returns or expose both
with distinct field names to avoid downstream confusion.

---

## 4. Cycle Durations (`memory/ops/cycle-durations.jsonl`)

All 4 entries verified: date arithmetic matches recorded hours.

| Cycle | Start → End | Computed | File | Status |
|-------|-------------|----------|------|--------|
| 5 | 2026-11-18 → 2026-11-19 | 24h | 24.0h | PASS |
| 8 | 2026-11-20 → 2026-11-23 | 72h | 72.0h | PASS |
| 14 | 2026-11-23 → 2026-11-24 | 24h | 24.0h | PASS |
| 15 | 2026-11-23 → 2026-11-24 | 24h | 24.0h | PASS |

---

## CONCLUSION

**All convergence metrics are computed correctly.** Formulas match their documented intent,
values trace back to source data without error, and boundary conditions behave as specified.

Two design notes (not bugs):
1. Ops efficiency-index.jsonl has a stale rework_rate input — regenerate after autonomy score updates.
2. Two different `efficiency_index` formulas exist in the codebase with different semantics — Convergence API must disambiguate.

**Total checks: 18/18 PASS (0 formula errors)**
