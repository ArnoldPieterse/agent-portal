# Claim-Phantom Report
Generated: 2026-11-24 03:32 by `memory/ops/verify_claims.py` (Builder).

Classifies every `verified:` marker in seat goal files against the disk:
  * REAL    - verified + a cited artifact exists on disk
  * PHANTOM - verified + cited path(s) present but NONE exist  (stale/false claim)
  * UNCITED - verified + no machine-checkable path (manual-only; needs a pointer added)

**Totals: 86 REAL, 0 PHANTOM, 12 UNCITED.**

## UNCITED verified claims (no path to check — add an artifact pointer so the ledger can close them)
- **archivist #5** Retrieval Accuracy Benchmark
- **archivist #8** Auto-Abstract Generation
- **archivist #9** Cross-Reference Consistency Check
- **verifier #1** Autonomous Remediation E2E
- **designer #1** Adaptive Information Density (Calm vs. Incident)
- **designer #2** Decision Provenance Overlay
- **designer #4** Predictive Risk Surface (Forward-Looking)
- **designer #5** Operator Emergency Brake UX
- **designer #6** Autonomy Confidence Decay Indicator
- **designer #7** Fleet Topology Live Graph
- **designer #8** Cross-Cycle Trend Strip
- **designer #9** Knowledge Impact Surface

## REAL claims (verified + artifact present)
- **orchestrator #4** Workload Rebalancer  -> `memory/orchestrator/auto_cycle_planner.py`
- **orchestrator #6** Context Budget Manager  -> `memory/orchestrator/context_budget.py`
- **orchestrator #8** Fleet Incident Auto-Responder  -> `memory/orchestrator/cockpit_validator.py`
- **researcher #1** Self-Healing Remediation Bus  -> `memory/researcher/remediation_bus.py`
- **researcher #2** Instrument ROI / Effort-Attribution Model  -> `memory/researcher/instrument_roi.py`
- **researcher #3** Goal-Dependency & Critical-Path Analyzer  -> `memory/researcher/goal_critical_path.py`
- **researcher #4** Calibration-to-Dispatch Feedback  -> `memory/researcher/calib_dispatch.py`
- **researcher #5** Blocker -> Catch -> Fix -> Verify Runbook  -> `memory/researcher/blocker-loop-runbook.md`
- **researcher #6** Research-Instrument Health Feed  -> `memory/researcher/instrument-health.json`
- **researcher #7** Whole-Cycle State Snapshot & Diff Store  -> `memory/researcher/cycle_snapshot.py`
- **researcher #8** Cockpit Data Golden-Fixture Regression  -> `memory/researcher/cockpit_golden.py`
- **researcher #9** Closed-Loop Failure-Mutation Library  -> `memory/researcher/failure_mutation.py`
- **researcher #10** Autonomy Guardrails & Blast-Radius Registry  -> `memory/researcher/blast_radius.py`
- **builder #1** Auto-Remediation Playbook Runner  -> `memory/builder/playbook_runner.py`
- **builder #2** Fleet Cockpit Frontend  -> `memory/builder/evidence-cockpit-frontend-2026-11-24.md`
- **builder #3** Model Swap Automation Script  -> `memory/builder/model_swap.py`
- **builder #4** Task Re-Router  -> `memory/builder/MEMORY.md`
- **builder #5** Health Score Widget  -> `memory/builder/evidence-cockpit-frontend-2026-11-24.md`
- **builder #6** Decision Log Viewer  -> `memory/builder/evidence-cockpit-frontend-2026-11-24.md`
- **builder #7** Auto-Cycle Trigger  -> `memory/builder/auto_cycle_trigger.py`
- **builder #8** Resource Monitor Panel  -> `memory/builder/evidence-cockpit-frontend-2026-11-24.md`
- **builder #9** Runbook Parser + Executor  -> `memory/builder/playbook_runner.py`
- **builder #10** Fleet State Snapshot Scheduler  -> `memory/builder/designer-goal2-fleet-states-2026-11-18.md`
- **builder #1** Closed-Loop Feedback Scorer  -> `memory/builder/loop_scorer.py`
- **builder #2** Adaptive Policy Tuner  -> `memory/builder/policy_tuner.py`
- **builder #3** Alert Correlation Engine  -> `memory/builder/alert_correlate.py`
- **builder #4** Fleet Capacity Predictor  -> `memory/builder/capacity_predict.py`
- **builder #5** Automated Chaos Drill Scheduler  -> `memory/builder/chaos_drill.py`
- **builder #6** Cockpit Topology Visualizer  -> `memory/builder/topology-visualizer-evidence-2026-11-24.md`
- **builder #7** Decision Audit Search Index  -> `memory/builder/decision_index.py`
- **builder #8** Post-Remediation Auto-Report  -> `memory/builder/post_mortem.py`
- **builder #9** Policy Conflict Detector  -> `memory/builder/policy_conflict.py`
- **builder #10** Cockpit One-Click Runbook Trigger  -> `memory/builder/evidence-runbook-trigger-2026-11-24.md`
- **archivist #1** Fact-Level Provenance Ledger  -> `memory/archivist/evidence-goal1-provenance-ledger-2026-11-23.md`
- **archivist #2** Stale-Knowledge Auto-Quarantine  -> `memory/archivist/auto_quarantine.py`
- **archivist #3** Knowledge Delta Feed  -> `memory/archivist/evidence-goal3-kb-delta-2026-11-23.md`
- **archivist #4** Cross-Agent Knowledge Conflict Resolver  -> `memory/archivist/conflict_resolver.py`
- **archivist #5** Decision-Knowledge Feedback Loop  -> `memory/archivist/evidence-goal5-kb-feedback-2026-11-23.md`
- **archivist #6** Knowledge Access Heatmap  -> `memory/archivist/access_heatmap.py`
- **archivist #7** Write-Time Auto-Linker  -> `memory/archivist/auto_linker.py`
- **archivist #8** KB Regression Sentinel  -> `memory/archivist/evidence-goal8-kb-sentinel-2026-11-23.md`
- **archivist #9** Tiered Summary Ladder  -> `memory/archivist/evidence-goal9-summary-ladder-2026-11-23.md`
- **archivist #10** KB Versioning & Rollback  -> `memory/archivist/evidence-goal10-kb-version-2026-11-23.md`
- **archivist #1** Knowledge Index Builder  -> `memory/archivist/knowledge-index.json`
- **archivist #2** Semantic Search Index  -> `memory/archivist/decay_production.py`
- **archivist #3** Citation Integrity Monitor  -> `memory/archivist/citation_monitor.py`
- **archivist #4** Knowledge Freshness Heatmap  -> `memory/archivist/freshness_heatmap.py`
- **archivist #6** Orphan Knowledge Recovery  -> `memory/archivist/dup_detect.py`
- **archivist #7** Knowledge Dependency Graph  -> `memory/archivist/knowledge-graph-v3.json`
- **archivist #10** Knowledge Base Health Report  -> `memory/archivist/weekly_digest.py`
- **scribe #1** Cycle Auto-Summary Generator  -> `memory/scribe/cycle_summary.py`
- **scribe #2** Fleet Decision Digest  -> `memory/scribe/decision_digest.py`
- **scribe #3** Cross-Agent Handoff Summarizer  -> `memory/scribe/handoff_summary.py`
- **scribe #4** Cockpit Narrative Layer  -> `memory/scribe/cockpit_narrative.py`
- **scribe #5** Blocker Resolution Tracker  -> `memory/ops/blockers.md`
- **scribe #6** Goal Completion Pattern Analysis  -> `memory/scribe/completion_patterns.py`
- **scribe #7** Fleet Knowledge Delta Report  -> `memory/scribe/knowledge_delta.py`
- **scribe #8** Runbook Lesson Extractor  -> `memory/scribe/runbook_lessons.py`
- **scribe #9** Stakeholder Briefing Generator  -> `memory/scribe/stakeholder_brief.py`
- **scribe #10** Synthesis Quality Metric  -> `memory/scribe/goal6-synthesis-quality-verified-2026-11-20.md`
- **verifier #1** Auto-Remediation Safety Gate  -> `memory/verifier/remediation_gate.py`
- **verifier #2** Cockpit Data Accuracy Test  -> `memory/verifier/cockpit_accuracy.py`
- **verifier #3** Remediation Rollback Test  -> `memory/verifier/rollback_test.py`
- **verifier #4** Decision Policy Compliance Audit  -> `memory/verifier/policy_audit.py`
- **verifier #5** Fleet State Consistency Check  -> `memory/verifier/state_consistency.py`
- **verifier #6** Auto-Cycle Trigger Validation  -> `memory/verifier/cycle_trigger_test.py`
- **verifier #7** Model Swap Verification Battery  -> `memory/verifier/model_swap_verify.py`
- **verifier #8** Health Score Regression Test  -> `memory/verifier/health_regression.py`
- **verifier #9** Task Re-Routing E2E Test  -> `memory/verifier/MEMORY.md`
- **verifier #10** Cockpit Performance Benchmark  -> `memory/verifier/cockpit_perf.py`
- **verifier #6** Failure Replay Harness  -> `memory/verifier/failure_replay.py`
- **verifier #7** Goal Lifecycle Audit  -> `memory/verifier/goal_lifecycle_audit.py`
- **verifier #8** Fleet Health Closed-Loop Test  -> `memory/verifier/fleet_health_closed_loop.py`
- **verifier #9** Cockpit A11y Gate (WCAG AA)  -> `memory/verifier/cockpit_a11y_gate.py`
- **verifier #10** Autonomy Precision/Recall Tracker  -> `memory/verifier/autonomy_pr_tracker.py`
- **designer #3** Multi-Goal Concurrency View  -> `memory/designer/acceptance-2-5-9-10-2026-11-19.md`
- **designer #10** Cockpit Cognitive Load Budget  -> `memory/designer/cognitive-budget.md`
- **mechanic #1** Auto-Failover Execution  -> `memory/mechanic/auto_failover.py`
- **mechanic #2** Model Load/Unload Automation  -> `memory/mechanic/model_lifecycle.py`
- **mechanic #3** Host Health Probe Suite  -> `memory/mechanic/circuit_breaker.py`
- **mechanic #5** Fleet State Collector Daemon  -> `memory/mechanic/state_collector.py`
- **mechanic #6** Model OOM Auto-Recovery  -> `memory/mechanic/oom_recovery.py`
- **mechanic #7** Scheduled Maintenance Window  -> `memory/mechanic/maintenance_window.py`
- **mechanic #8** Host Capacity Arbitration  -> `memory/mechanic/capacity_arbiter.py`
- **mechanic #9** Incident Auto-Classification  -> `memory/mechanic/incident_classifier.py`
- **mechanic #10** Portal Self-Healing  -> `memory/mechanic/portal_heal.py`
