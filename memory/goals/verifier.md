# Verifier - Cycle 16 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Cycle Transition, (2) Self-Validation Circuit, (3) Adaptive Topology

1. **Self-Validation Auditor** - memory/verifier/selfval_audit.py: for each goal marked reached this cycle, check evidence file exists + has PASS marker + test is importable/syntactically valid. Report violations to memory/verifier/selfval-report.md. Verified: on current data 0 violations; on synthetic data with missing evidence, flags correctly. (pointer: memory/verifier/MEMORY.md)

2. **Cycle Transition Validator** - memory/verifier/cycle_transition_test.py: simulate full transition (100% -> archive -> new goals). Verify old files in archive/, new files valid format, TODO.md updated, no data loss. Verified: after simulated transition all 8 agents have valid goal files; archive has 8 new files. (pointer: memory/verifier/evolution-lifecycle-validator-2026-11-17.md)

3. **Dispatch Fuzzer v2 (Topology-Aware)** - extend dispatch_fuzzer.py: add seat-matrix awareness. Generate scenarios with random unreachable seats; verify dispatch routes to backups, no passes wasted on dead seats. Verified: 50 random topologies, 0 dispatches to unreachable seats. (pointer: memory/verifier/dispatch_fuzzer.py)

4. **Goal Quality Gate** - memory/verifier/goal_quality_gate.py: for each goal in new cycle file check: (a) has "Verified:" sentence, (b) references specific file/command, (c) <=500 chars. Score 0-10; reject if <6. Verified: well-formed goals score >=8; vague goals score <=4. (pointer: memory/verifier/MEMORY.md)

5. **Evidence Integrity Checker** - memory/verifier/evidence_integrity.py: for all "verified:" markers, check referenced artifact exists + mtime after cycle start. Flag stale evidence from prior cycles. Verified: clean data = 0 flags; synthetic old mtimes correctly identified. (pointer: memory/verifier/evidence-integrity-drift-2026-11-22.md)

6. **Autonomous Round E2E Test** - memory/verifier/auto_round_test.py: run full protocol (trigger->archive->propose->validate->write) in sandbox dir. Verify end-to-end valid state, no files lost, TODO.md well-formed. Verified: passes on clean slate; idempotent (second run detects "already done"). (pointer: memory/verifier/MEMORY.md)

7. **Seat Matrix Validator** - memory/verifier/seat_matrix_check.py: validate seat-matrix.json: all 8 agents present, host in known set, state in {ready,unreachable,loading}, last_seen valid ISO-8601. Hook into every write. Verified: valid passes; each corrupted field -> specific error. (pointer: memory/verifier/MEMORY.md)

8. **Cycle Duration Regression** - compare actual cycle duration vs forecast (cycle_forecast.json). If actual >1.5x forecast, flag regression + log to memory/verifier/duration-regressions.md. Verified: synthetic actual=2xforecast triggers flag; actual~forecast no flag. (pointer: memory/verifier/regression-suite-goal1-evidence-2026-11-20.md)

9. **Validation Coverage Report** - for each current-cycle goal, check if test script exists at implied path. Report coverage % with pass/fail/missing per goal. Verified: report lists all goals with status; coverage % accurate.

10. **Fleet Autonomy Regression Battery** - memory/verifier/autonomy_battery.py: single script running ALL checks (goals 1-9) as a suite. Exit 0 if all pass, exit 1 with specific failures. The "regression gate" for autonomy features. Verified: healthy system = exit 0; one broken component = exit 1 + correct error.
