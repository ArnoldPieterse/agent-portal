# Convergence Model (G1) — Input Data Gap Report
Author: Orchestrator (assist, credit Researcher G1). Date 2026-11-25.
Purpose: unblock `convergence_model.py` input; replace the recurring "cycle-durations.jsonl has no completion_pct" blocker with a precise, owned next step.

## Consolidated input (SSOT)
`memory/ops/cycle-history-consolidated.jsonl` — one row per cycle, fields:
cycle, duration_hours, completion_pct, intervention_count, closure_evidence, reliability, provenance{...}.
Every value carries provenance; no field is fabricated. Regenerate: `python memory/orchestrator/consolidate_cycle_history.py` (idempotent).

## Key finding (the real blocker)
Archived goal files are **point-in-time snapshots**, not closure records. A naive reached-marker count yields 0%→100% for cycles that all plausibly completed:
- cycle 9 = 6.7%, cycle 13 = 1.4%, cycle 16 = 5.0% ⇒ snapshots captured at GOAL-SETTING, not closure.
- cycle 15 = 91.1% ⇒ snapshot captured AFTER closure (has closeout evidence).
So completion_pct is only trustworthy where explicit **closure evidence** exists (closeout / all-N-complete / -closed- / full-closure / reverified).

## Reliability tiers (current)
| tier | cycles | have all 3 fields |
|------|--------|-------------------|
| HIGH (closure + dur) | 5, 14, 15 | yes — 3 cycles |
| MED (closure, no duration) | 10, 12 | completion+interventions; missing duration_hours |
| LOW (snapshot-only, unreliable %) | 7, 8, 9, 13, 16 | not fit for R² |
| partial | 2, 3, 17 | missing fields |

## What G1's acceptance test needs vs has
- Needs: **12+ cycles** with duration + completion% + interventions to reach R²>0.7.
- Has (high-reliability): **3** (cycles 5, 14, 15).
- Gap: **9 more high-reliability cycles.**

## Exact next step (durable fix, owned)
1. **Mechanic — Cycle Duration Ops Tracker** (its open goal #3): log `duration_hours` per cycle to cycle-durations.jsonl going forward AND backfill closed cycles 8, 10, 12 from archive start/end dates. This fills the MED tier → HIGH.
2. **Add a closeout `completion_pct` field** (reached/total at cycle end) to each lane's closeout so completion_pct is recorded AT closure, not scraped from mid-cycle snapshots. Until then, only trust the HIGH/MED rows above.
3. Re-run consolidation after (1); G1 can then fit on 6–8 high-reliability cycles and state R² honestly instead of being blocked.

## Do NOT
- Do NOT feed LOW-tier completion_pct (9/13/16) into the model — they encode snapshot timing, not cycle outcome; this is what produced the spurious "convergence" dips.

<!-- pointer: parent memory/researcher/INDEX.md · sibling memory/ops/cycle-history-consolidated.jsonl -->
