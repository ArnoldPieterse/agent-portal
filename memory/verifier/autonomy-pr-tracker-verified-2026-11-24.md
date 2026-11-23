# Autonomy Precision/Recall Tracker — VERIFIED 2026-11-24

## Summary
Goal #10 (Cycle-14): **Autonomy Precision/Recall Tracker** — classify each autonomous action as correct/false-positive/false-negative; weekly metric.

## Verification
- `autonomy_pr_tracker.py --self-test`: **7 PASS / 0 FAIL** from BOTH repo root and memory/verifier (CWD-independent, all paths __file__-anchored)
- T1: All-correct log → P=1.0 R=1.0 F1=1.0
- T2: Mixed log (2TP/1FP/1FN) → P≈0.667 R≈0.667
- T3: Empty log → defaults, no division by zero
- T4: Fault without action → false_negative
- T5: Action without fault → false_positive
- T6: Live audit against decision-log.jsonl (8 actions)
- T7: Window filtering excludes old entries

## Key Design
- Classification logic: has_fault + has_action + recovered = TP; no_fault + action = FP; fault + no_recovery = FN
- Metrics: precision, recall, F1 with safe division defaults
- Weekly window (configurable via --window) filters by ts field
- Reads from decision-log.jsonl at repo root

## Artifact
memory/verifier/autonomy_pr_tracker.py (10370 bytes)
