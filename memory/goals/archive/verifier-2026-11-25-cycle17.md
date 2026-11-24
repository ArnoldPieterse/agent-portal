# Verifier — Cycle 17 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence** (productionize/operate phase - fleet converging to ~100%; built capabilities now must RUN autonomously as scheduled tasks with monitoring + self-heal)
Pillars: (1) Scheduled-task health, (2) Drift/self-heal verification, (3) Terminal stability + autonomy safety

1. **Scheduled-Task Health Watchdog** - `python memory/verifier/schtask_watchdog.py`: verify every schtask in the fleet's scheduled-background list actually fires on cadence and exits 0; detect missed/delayed/stuck tasks by comparing expected interval vs last-run timestamps. Verified: all expected tasks present + firing within tolerance; a synthetic missed-task (stale last-run) is correctly flagged with task name + age.

2. **Mirror-Sync Drift Detector Productionization** - the cycle-2 SMB drift detector now runs as a scheduled task (every 30 min); verify schtask `PortalSmbDrift` is registered, fires on cadence, appends to the drift log, and auto-alerts on threshold breach. Verified: schtask present + last-run within interval; drift log receiving entries; a synthetic divergence event triggers an alert record.

3. **Self-Heal Loop Verification** - `python memory/verifier/heal_loop_verify.py`: verify the self-healing mirror (every 15 min) detects a forced divergence and re-syncs automatically with no human action; force a divergence, observe auto-repair within one cycle, confirm repair is logged and does not over-correct. Verified: forced divergence auto-repaired in <15 min; repair entry written; target file byte-identical to source post-heal.

4. **Production SLA Enforcement Test** - `python memory/verifier/prod_sla.py`: now that systems run as scheduled tasks, verify each has a measured SLA (fire-interval, exit-code, duration); produce a per-task compliance table and flag breaches with timestamp. Verified: compliant tasks pass; a synthetic late-firing task is flagged with the breach window.

5. **Autonomy Convergence End-State Verification** - `python memory/verifier/convergence_endstate.py`: forecast shows ~100% by 11-25; verify the terminal converged state is STABLE (not oscillating): over a sustained N-cycle window, mode stays IDLE/MAINTENANCE, no goal re-opens, no phantom dispatch. Verified: window shows stable terminal mode; zero regressions/re-open events.

6. **Drift-Log Review Automation** - `python memory/verifier/drift_review.py`: the proposal leaves "two weeks of drift-log review"; automate it: parse accumulated drift-log entries, classify each (benign sync-lag vs real divergence), emit a weekly summary + verdict + escalation list. Verified: all current entries classified; an injected real-divergence entry is correctly escalated to the alert path.

7. **Scheduled-Task Dependency Integrity** - `python memory/verifier/task_dep_check.py`: verify the scheduled-task dependency/blast-radius graph matches reality — every declared dependency exists and fires in order; detect orphan tasks or broken chains. Verified: current graph consistent (no orphans/broken deps); a synthetic removed-dependency is correctly detected as a broken chain.

8. **Chaos-Drill Recovery Verification** - `python memory/verifier/chaos_recovery.py`: verify the monthly chaos drill (kill portal on a rotating host) actually recovers: after forced kill, portal restores within SLA and data is intact; inspect recovery logs + re-probe endpoints post-drill. Verified: last drill recovered within SLA with zero data loss; a synthetic slow-recovery case is flagged as an SLA breach.

9. **Budget-Exhaustion Graceful-Degrade Test** - `python memory/verifier/budget_degrade.py`: when the autonomous pass budget is exhausted, verify the fleet degrades gracefully (clean stop, state persisted, correct resume) rather than corrupting mid-operation. Verified: simulated exhaustion -> clean stop; state file valid; resume completes without re-doing already-finished work (idempotent resume).

10. **Verifier Self-Coverage Audit** - `python memory/verifier/self_coverage.py`: meta-check that the verifier lane's test surface has no gaps — map every productionized scheduled task + autonomous behavior to at least one running verification goal/script; report coverage % + named uncovered items as follow-ups. Verified: current coverage measured and reported; each newly-identified gap is a named, addressable follow-up (not silently dropped).
