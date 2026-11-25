# Autonomy Handoff Protocol
**Scribe goal #9** | **Date:** 2026-11-25
Defines the protocol for when an agent's automation replaces a human step.

## 1. Required Evidence (Before/After Metrics)

Every handoff requires paired measurements:

| Metric | Before (human-in-loop) | After (autonomous) | Source |
|--------|----------------------|-------------------|--------|
| Intervention count/cycle for this class | N_human | N_auto | memory/scribe/intervention-patterns.jsonl |
| Time-to-completion (median) | T_human | T_auto | cycle-durations or task logs |
| Error/rework rate | R_human | R_auto | rework_score in autonomy-trend.jsonl |

**Example from existing data:**
- Portal recovery: Before = human restarts portal on each crash (~2x/week, 5min manual). After = boot_recovery.py + portal_watchdog.py auto-restart (0 interventions since 2026-11-14). Evidence: decision-autonomy-map.jsonl entry `dec-2026-11-14-portal-recovery`.

## 2. Recording Format

When a handoff occurs, record in **two places**:

### 2a. Decision log (memory/synthesis/decisions.jsonl)
```json
{"id": "dec-YYYY-MM-DD-<slug>", "date": "YYYY-MM-DD", "decision": "<what was automated>", "source": "<who proposed>", "automation_built": [{"file": "<path>", "role": "<what it does>"}], "intervention_class_removed": "<class name>", "evidence_before": {...}, "evidence_after": {...}}
```

### 2b. Autonomy trend (memory/scribe/autonomy-trend.jsonl)
Append the new cycle's score with updated component_breakdown reflecting the eliminated intervention class. The `pass_autonomy` component should increase.

### 2c. Causal map (memory/scribe/decision-autonomy-map.jsonl)
Add a chain entry linking decision → automation file → intervention class → score contribution.

**Example:** The evolution CLI handoff (dec-2026-11-16-evolution-cli) was recorded in all three: decisions.jsonl entry 7, causal map entry 2, and the autonomy trend shows pass_autonomy jumping from 45.0→58.3 between cycles 5 and 17.

## 3. Verification Criteria (N Consecutive Cycles Without Regression)

A handoff is **confirmed** when:
- **N = 3 consecutive cycles** where the eliminated intervention class has 0 occurrences in intervention-patterns.jsonl
- The autonomy score component that benefited from the handoff does not regress below its post-handoff value for those 3 cycles
- No new "rework" events are attributed to the automated step (checked via rework_score stability)

**If regression occurs:**
1. Flag in memory/ops/anomalies.jsonl (type: "handoff_regression")
2. Revert to human-in-loop for that specific step
3. Record the failure mode in decisions.jsonl as a new entry with `"status": "reverted"`
4. The causal map entry gets `"regressed_at_cycle": N`

**Current status of known handoffs:**
| Handoff | Since | Cycles clean | Status |
|---------|-------|-------------|--------|
| Portal recovery (Mechanic) | 2026-11-14 | 8+ | CONFIRMED |
| Evolution CLI (Builder/Verifier) | 2026-11-16 | 7+ | CONFIRMED |
| Pointer-map audit (Archivist) | 2026-11-13 | 9+ | CONFIRMED |

## Summary Rule

> An automation "replaces" a human step only after 3 clean cycles. Until then, it's "assisting," not "replacing." The distinction matters for the autonomy score: assisting = +0.5 weight, replacing = full weight.
