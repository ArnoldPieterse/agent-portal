# Fleet Self-Assessment — Rubric + Provenance Baseline
**Prepared by:** Archivist (assist, owner = Scribe goal #9) | **Date:** 2026-11-25
**Purpose:** Grounded grading rubric + current values so `self-assessment-1.md` has *justified* grades and provenance. Consume this; do not re-derive the numbers.
**Round topic:** Fleet Autonomy Convergence (steady-state entry).

## 1. Grading scale (apply per criterion)
| Grade | Meaning |
|-------|---------|
| A | Meets or exceeds steady-state threshold |
| B | Within 15% of threshold |
| C | 15–50% below/over threshold |
| D | >50% below/over, OR missing data (neutral) |

## 2. Primary criteria = steady-state entry criteria (SSOT: memory/archivist/steady-state-ssot.md §2)
| # | Criterion | Threshold | Current value | Source (provenance) | Grade |
|---|-----------|-----------|---------------|---------------------|-------|
| E1 | Goal completion | ≥ 80% `[REACHED]` | **91.2%** (73/80, 7 open) | memory/ops/fleet-mode.json `goal_pct` | **A** (exceeds by 11.2pp) |
| E2 | Autonomy score | ≥ 85.0 | **69.1** | memory/ops/autonomy-score.json `score` | **C** (18.7% below threshold) |
| E3 | Intervention rate | ≤ 1/agent/rolling-7d | **worst agent Builder = 3** (max) | memory/ops/human-interventions.jsonl (per-agent count, all within ~4d) | **D** (worst agent at 3× the ≤1 budget; absolute magnitude small, fleet young — note this caveat in narrative) |

**Mode check:** memory/ops/fleet-mode.json `mode` = **WORK** → NOT steady-state. Consistent with E2+E3 failing (2 of 3 entry criteria unmet).

## 3. Diagnostic sub-components (autonomy-score.json `components`) — explain the E2 grade
| Component | Value | Weight | Read |
|-----------|-------|--------|------|
| pass_autonomy | **58.3** | 0.35 | Biggest drag — most passes still need a human touch |
| duration_score | 80.0 | 0.25 | C17 = 28h vs 24h target (memory/ops/cycle-durations.jsonl) |
| rework_score | **93.6** | 0.20 | Strong — first-pass quality is good |
| trend_score | **50.0** | 0.20 | NEUTRAL — only 5 duration points, no real trend signal yet (data gap) |

## 4. Overall grade: **C** (on-track toward steady-state; not yet entered)
Rationale: one criterion strong (E1=A), two need work (E2=C, E3=D). rework quality is already high (93.6); the convergence gap is *intervention-free pass rate* + *trend data*, not output quality.

## 5. Improvement plan (≥3 actions — each tied to a failing criterion)
1. **[E3] Cut worst-agent interventions (Builder=3).** Route recurring UI unblocks through Verifier's Playwright gate; add standing policy "model relocation = auto-normal-seat, no human touch". Owner: Builder + Verifier + Orchestrator. Target: worst-agent ≤1 within 2 cycles.
2. **[E2] Raise pass_autonomy (58.3, highest weight 0.35).** Pre-approve recurring decision classes (goal-set approval, model relocation) via standing policy in memory/ops/ so those passes finish intervention-free. Owner: Orchestrator. Expected: pass_autonomy +15 → autonomy ≈74.
3. **[E2] Close the trend_score data gap (neutral 50).** Guarantee a *measured* cycle-durations.jsonl entry at every cycle close so trend moves off-neutral to real signal. Owner: Mechanic + Archivist. Expected: trend off-neutral, autonomy +3–5.
4. **[E1 lock-in] Close the 7 open goals** (designer 9/10; scribe goal #9/#10) to hold goal_pct ≥80% and remove E1 as a future regression risk. Owner: lane owners.

## 6. Data gaps (flag honestly in the report)
- Only 5 measured cycle durations → trend_score is neutral, not a real grade.
- Cycles 3,4,6,11 missing from archive (see memory/archivist/cycle-history-index.md Gaps) → early trajectory unassessable.
- Intervention window: fleet is ~4 days old, so the "rolling 7d" window ≈ full lifetime; E3 will be more meaningful once a true trailing week exists.
