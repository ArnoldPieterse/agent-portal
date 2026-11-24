# Verifier — Cycle 15 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Mode Controller, (2) Dispatch Correctness, (3) Idle Productivity

1. **Mode Transition Integration Test** - `python memory/verifier/mode_transition_test.py`: simulate fleet going 99%->100% and verify: (a) fleet-mode.json updates within one pass cycle, (b) dispatch text changes from goal-list to maintenance-task, (c) cockpit banner color changes (check API response). Verified: all 3 assertions pass on simulated transition; total test <2 min; test is idempotent (can run repeatedly without side effects).
   [REACHED 2026-11-24] (pointer: memory/verifier/mode_transition_test.py)

2. **Idle Pass Auditor** - `python memory/verifier/idle_audit.py`: scan last 50 auto-loop passes from autoloop.jsonl. Flag any pass where: (a) agent dispatched for a reached goal, OR (b) agent received generic (a)(b)(c)(d) menu when fleet_mode was MAINTENANCE/IDLE. Write report to memory/verifier/idle-audit-report.md with violation count + specific pass IDs. Verified: on current post-fix data, reports 0 violations; on synthetic pre-fix data, correctly flags >=5 violations. (pointer: memory/verifier/MEMORY.md)

3. **fleet-mode.json Schema Validator** - `python memory/verifier/mode_schema_check.py`: validate fleet-mode.json structure: mode is one of {WORK, MAINTENANCE, IDLE}, timestamp is valid ISO-8601, goal_pct is float 0-100, last_activity is ISO-8601. Run on every write (hook into fleet_mode_writer). Verified: valid file passes; each field corrupted individually causes failure with specific error message; validator runs <100ms.
   [REACHED 2026-11-24] (pointer: memory/verifier/mode_schema_check.py)

4. **Dispatch Correctness Fuzzer** - `python memory/verifier/dispatch_fuzzer.py`: generate 100 random goal-state configurations (mix of reached/open, various modes); for each, run dispatch_filter and assert: no reached goal appears in output; in MAINT/IDLE, output matches rotation table. Verified: 100/100 random configs produce correct dispatch; any violation causes test failure with the specific config that failed.
   [REACHED 2026-11-24] (pointer: memory/verifier/dispatch_fuzzer.py)

5. **Pass Budget Compliance Test** - `python memory/verifier/budget_compliance.py`: simulate 250 passes (budget=200); verify: (a) counter increments correctly each pass, (b) at pass 200, BUDGET_EXHAUSTED returned, (c) no pass >200 is dispatched, (d) mode transitions to IDLE at exhaustion. Verified: all 4 assertions pass; counter never exceeds budget; no off-by-one errors at boundary.
   [REACHED 2026-11-24] (pointer: memory/verifier/budget_compliance.py)

6. **Mode Race Condition Test** - `python memory/verifier/mode_race_test.py`: simulate two concurrent mode-change triggers (e.g., goal reaches 100% AND 6h timer fires simultaneously). Verify: fleet-mode.json ends in a valid state (not corrupted/partial); exactly one transition is logged; no deadlock. Verified: 50 concurrent-trigger simulations all produce valid final state; JSONL has exactly 1 entry per simulation; test completes <30s. (pointer: memory/verifier/MEMORY.md)

7. **Productivity Metric Validator** - `python memory/verifier/productivity_validate.py`: given autoloop.jsonl + known ground-truth file changes, verify productivity_counter output matches expected rates within 1%. Test with: all-productive, all-wasted, mixed (known ratio). Verified: 3 test scenarios produce correct rates; any discrepancy >1% causes failure with expected vs actual values shown.
   [REACHED 2026-11-24] (pointer: memory/verifier/productivity_validate.py)

8. **Cycle Transition Rollback Test** - `python memory/verifier/cycle_rollback_test.py`: simulate failed cycle transition (e.g., new goal file write fails mid-sequence). Verify: (a) old goals still readable from archive, (b) no partial state (either fully transitioned or not), (c) error is logged with specific step that failed. Verified: on simulated failure at step 3 of 5, old files intact; no orphaned new files; error log identifies step 3.
   [REACHED 2026-11-24] (pointer: memory/verifier/cycle_rollback_test.py)

9. **Stale Dispatch Detector** - `python memory/verifier/stale_dispatch.py`: scan current dispatch queue; flag any entry referencing a goal with status="reached" AND reached_at >1h ago (stale). Write count + specific stale entries to memory/verifier/stale-dispatch-report.md. Verified: on clean data, reports 0 stale; on data with 3 artificially-stale entries, detects all 3 with correct goal IDs. (pointer: memory/verifier/scribe-goal2-v2-reconciliation-2026-11-18.md)

10. **End-to-End Mode Cycle Test** - `python memory/verifier/e2e_mode_cycle.py`: full simulation: WORK (5 open goals) -> complete goals -> MAINTENANCE (6h wait) -> IDLE -> new cycle starts -> WORK again. Verify all transitions, dispatch changes, banner updates, and productivity tracking throughout. Verified: complete cycle runs <5 min; every state transition produces correct artifacts; no assertion failures across all 4 mode phases. (pointer: memory/verifier/MEMORY.md)
