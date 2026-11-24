# Researcher — Next-Cycle Goal Proposal (2026-11-24)

Round topic: **Closed-Loop Autonomy & Fleet Cockpit**

## What was done this pass
- Archived the completed prior set (all 10 verified) to `memory/goals/archive/researcher-2026-11-24.md`.
- Wrote the fresh proposal to `memory/goals/researcher.md`: **10 new goals**, each traceable to the round topic, none re-issuing the prior 10 (remediation_bus / instrument_roi / goal_critical_path / calib_dispatch / blocker-loop-runbook / instrument_health / cycle_snapshot / cockpit_golden / failure_mutation / blast_radius) nor any closed anti-repeat topic.

## The 10 proposed goals (verbatim short titles, for Orchestrator collection)
1. Fleet Observability Completeness Baseline — fix 3-of-4 hosts permanently null; per-host metric-coverage KPI.
2. Freshness-Stamping Contract + Verification Harness — source-time vs write-time ts; catches fresh-mtime/stale-ts (F3 class).
3. Cockpit Data Lineage Map + Drift Detector — document hops + stamping owners; detect doc↔actual drift.
4. Seat Capability / Automation-Path Matrix — which paths work from which seat; route blocked work to capable seat.
5. Watchdog Threshold Calibration from History — data-driven detection thresholds (stall/staleness) vs guessed constants.
6. Fleet Convergence Predictor — aggregate time-to-all-clear ETA + confidence band from closure velocity.
7. Loop-Closure Rate KPI — per-instrument + fleet-wide closed-vs-reopened rate on real production loops.
8. Self-Heal Counterfactual Simulator — replay remediation actions vs historical snapshots; act-early/never deltas.
9. Cockpit Data Trust Score — single 0-1 banner indicator (freshness+completeness+closure).
10. Closed-Loop Telemetry Contract Validator — standardize + validate the unified event schema {detection,action,verification,closure,reopen}.

## Rationale (why these are the right next targets)
Last cycle's ACT/MEASURE layer is done; what was provably BLIND: (a) 3/4 hosts emit zero metrics (sensing gap), (b) feed mtime fresh but ts 10h stale (stamping contract), (c) no aggregate convergence/closure signal, (d) no routing by seat capability. These 10 close exactly those gaps.

## Anti-repeat check
Confirmed none overlap the prior-10 goal signatures nor the closed anti-repeat list (Unified Loader LIVE / Residency Matrix / Overnight Unload / Evidence Freshness SLA / Cross-Host Benchmark / Fleet KG v2 / Reproducibility Protocol / Slip Prediction v2 / Source Reliability Scoring / Blocker Triage Automation).

Confidence: HIGH on scope/distinctness (verified against both lists this pass). Implementation not yet started — these are PROPOSED for next cycle.
