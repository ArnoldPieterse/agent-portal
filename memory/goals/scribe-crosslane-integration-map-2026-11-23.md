# Cross-Lane Integration Map — Closed-Loop Autonomy & Fleet Cockpit (2026-11-23)

**Scribe synthesis.** How the 4 active lanes' OPEN goals interlock into one closed loop; dependency edges; who owns the next action. Source = on-disk goal files (memory/goals/{builder,verifier,designer,researcher}.md), not the dispatch prompt.

## The loop (stage -> owning open goals)

1. **DETECT/MONITOR** — Verifier #2 Cockpit Live-Staleness Monitor; Verifier #3 Autonomy Stall Detector; Researcher #6 Research-Instrument Health Feed.
2. **DIAGNOSE/CORRELATE** — Researcher #5 Blocker->Catch->Fix->Verify Runbook (links each OPS-NOTE to its detector); Researcher #10 Autonomy Guardrails & Blast-Radius Registry.
3. **REMEDIATE** — Researcher #1 Self-Healing Remediation Bus (applies safe idempotent fixes); Builder #9 Runbook Parser + Executor; Builder #10 Fleet State Snapshot Scheduler.
4. **VERIFY (loop closes here)** — Verifier #1 Autonomous Remediation E2E (detect->diagnose->remediate->verify, per-stage SLA); Verifier #4 Closed-Loop Latency Budget; Researcher #8 Cockpit Data Golden-Fixture Regression.
5. **LEARN/SCORE** — Researcher #2 Instrument ROI / Effort-Attribution; Researcher #4 Calibration-to-Dispatch Feedback; Researcher #3 Goal-Dependency & Critical-Path Analyzer.
6. **PRESENT (cockpit)** — Designer #1 Adaptive Density; #2 Decision Provenance Overlay; #4 Predictive Risk Surface; #5 Operator Emergency Brake; #6 Confidence Decay Indicator.

## Critical path (the spine of "closed-loop autonomy")

```
Researcher #1 Remediation Bus  ->  Builder #9 Runbook Executor  ->  Verifier #1 Autonomous Remediation E2E
        (something to fix)            (applies the fix)              (proves detect->remediate->verify)
```
Verifier #1 CANNOT reach its acceptance test until Researcher #1 + Builder #9 land — it needs a real remediation to exercise. This is the single longest dependency chain in the round.

## Independent / unblockable now (no upstream dep)
- Verifier #2 Staleness Monitor + #3 Stall Detector — pure sensors; give the loop its eyes immediately.
- Researcher #5 Blocker Runbook — self-contained on memory/ops/blockers.md.
- Designer #4 Predictive Risk Surface — consumes existing memory/goals/next10.json (already generated); no build dep.
- Designer #5 Emergency Brake — standalone UX pattern.

## Next-action owners (unblock order)
1. **Researcher** -> land #1 Remediation Bus first; it unblocks BOTH Verifier #1 and the Builder executor loop.
2. **Verifier** -> land #2 + #3 now (independent sensors) so the loop has detection before remediation lands.
3. **Designer** -> land #4 Predictive Risk Surface (reads existing next10.json) for a visible cockpit win with zero build dep.

## Flag — dispatch prompt vs disk contradiction (NOT resolved, no side picked)
The auto-loop dispatch prompt lists Builder's open goals as {Closed-Loop Feedback Scorer, Adaptive Policy Tuner, Alert Correlation Engine, Fleet Capacity Predictor, Automated Chaos Drill Scheduler}. But memory/goals/builder.md on disk is the cycle-10 set with only #9 Runbook Parser + Executor and #10 Fleet State Snapshot Scheduler open. These do not match: either a newer cycle-11 builder goal file was intended but never written to disk, or the dispatch prompt is stale. This map uses the on-disk file as source of truth. Orchestrator should reconcile before the next goal-setting round.

---
*Written by Scribe, 2026-11-23. No claims invented — every goal title traces to the named lane's on-disk goal file.*
