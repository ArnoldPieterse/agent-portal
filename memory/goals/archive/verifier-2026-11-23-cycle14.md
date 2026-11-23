# Verifier - 10 goals (set 2026-11-23, cycle-14)

Focus: Closed-Loop Autonomy & Fleet Cockpit. Cycle 14 proves the closed loop actually closes: every decision leads to a verified outcome, and the cockpit shows truth not fiction.

1. **Closed-Loop End-to-End Test** - `python memory/verifier/e2e_loop_test.py`: full pipeline test: trigger degradation -> verify detection (<60s) -> verify decision made (<30s) -> verify action executed (<120s) -> verify recovery confirmed (<60s) -> verify complete log entry exists. Score each stage pass/fail + latency. Verified: 5 different degradation types tested; all stages pass for at least 4/5; any failure is logged with exact stage and timing.

2. **Cockpit Data Integrity Test** - `python memory/verifier/cockpit_integrity.py`: verify /api/cockpit (or aggregator output) matches ground truth: goal counts match files, agent status matches probes, resource data matches actual usage, decision log entries are complete. Run on every snapshot. Verified: 3 integrity checks defined; a deliberately corrupted source file is detected as mismatch; all checks pass on clean state.

3. **Remediation Safety Test** - `python memory/verifier/remediation_safety.py`: verify remediation actions never make things worse: for each action type, simulate execution against a known-bad state and verify rollback triggers if post-verification fails. No cascade failures allowed. Verified: 3 action types tested against bad states; all trigger rollback within 30s; no state is left worse than pre-action in any case.

4. **Decision Correctness Benchmark** - `python memory/verifier/decision_benchmark.py`: given N known-degraded scenarios (with ground-truth correct actions), verify the decision pipeline picks the right action. Track accuracy over time; alert if <90%. Emit benchmark results per scenario. Verified: >=10 scenarios defined with known-correct answers; accuracy computed and reported; a scenario where wrong action is chosen is logged with expected vs actual.

5. **Recovery Time Objective (RTO) Test** - `python memory/verifier/rto_test.py`: for each failure mode (agent crash, host down, OOM, network partition), measure actual time from trigger to full recovery. Compare against RTO targets. Alert if any exceeds target by >20%. Verified: 4 failure modes tested; RTO measured for each; results compared to targets in memory/verifier/rto-targets.json; violations flagged.

6. **Cockpit UI Regression Test** - `python memory/verifier/cockpit_ui_test.py`: Playwright test suite against cockpit: all panels render with data, no JS errors in console, interactions work (expand/collapse, filter, navigate), responsive at 1024px and 1400px. Verified: >=8 UI assertions pass; a deliberately broken panel (missing data source) is detected as blank/error; test runs in <60s.

7. **Cascade Containment Test** - `python memory/verifier/cascade_test.py`: simulate agent N failing mid-task; verify: dependent tasks are paused (not crashed), no orphaned processes, automatic recovery begins when N returns, no data corruption from partial task completion. Verified: 3 cascade scenarios tested; in all cases no crash propagates beyond N's direct dependents; recovery is automatic within RTO.

8. **Audit Log Completeness Check** - `python memory/verifier/audit_check.py`: verify every entry in the decision audit log has ALL required fields: trigger_id, timestamp, agent, context_snapshot, decision, action_taken, outcome, verification_result. Flag any incomplete entries. Verified: check runs against full log; a deliberately incomplete entry is flagged with missing fields listed; 100% of complete entries pass validation.

9. **Idempotency Verification** - `python memory/verifier/idempotency_test.py`: for each remediation action type, execute it twice in succession against the same state; verify second execution is a no-op (no additional changes, no errors). Verified: 4 action types tested; second execution produces zero state diff; no error or partial state from double-execution.

10. **Cockpit Load & Concurrency Test** - `python memory/verifier/load_test.py`: simulate 50 concurrent API clients hitting cockpit endpoints with mixed read patterns; verify p95 <200ms, no 5xx errors, no data corruption (concurrent reads see consistent snapshots). Verified: 50 concurrent clients for 60s; p95 measured and reported; zero 5xx responses; spot-check of 10 random responses shows internally consistent data.
