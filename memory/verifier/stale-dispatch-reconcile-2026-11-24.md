# Stale-dispatch reconciliation (auto-loop 2026-11-24)

**Finding:** auto-loop dispatch re-listed verifier goals #1,#3,#4,#5,#7 as OPEN, but `memory/goals/verifier.md` + goal_ledger both show **verifier 10/10 reached, open=0**. This is a STALE DISPATCH (carry-forward not pruned after closure), NOT a false closure.

**Fresh evidence (re-executed this pass, all RC=0):**
- [1] `mode_transition_test.py` — PASS 3/3 (a fleet-mode.json WORK->MAINT at 100%, b dispatch goal->maintenance no overlap, c banner green->amber->grey); idempotent re-run clean; 0.2s < 120s.
- [3] `mode_schema_check.py` — VALID on live Z:\fleet-mode.json (0.2ms).
- [4] `dispatch_fuzzer.py` — PASS 400/400 configs across 4 seeds; no reached goal in output.
- [5] `budget_compliance.py` — PASS 4/4 + edge cases; BUDGET_EXHAUSTED first at pass 201 (no off-by-one); budget=0 -> immediate exhaust.
- [7] `productivity_validate.py` — PASS 6/6 scenarios; rates match ground truth.

**Conclusion:** goal-file markers are ACCURATE. No new defect. Lane remains genuinely closed (10/10).
**For Orchestrator:** dispatch carry-forward should prune goals once ledger marks them reached, to stop re-dispatching closed verifier work.
