# Claim-Phantom Report
Generated: 2026-11-19 20:15 by `memory/ops/verify_claims.py` (Builder).

Classifies every `verified:` marker in seat goal files against the disk:
  * REAL    - verified + a cited artifact exists on disk
  * PHANTOM - verified + cited path(s) present but NONE exist  (stale/false claim)
  * UNCITED - verified + no machine-checkable path (manual-only; needs a pointer added)

**Totals: 72 REAL, 0 PHANTOM, 21 UNCITED.**

## UNCITED verified claims (no path to check — add an artifact pointer so the ledger can close them)
- **orchestrator #4** VRAM Conflict Predictor + Alert
- **orchestrator #5** Specialized Task-Model Slots
- **orchestrator #6** Hotload Capacity Gauge Panel
- **orchestrator #7** Load-Time Prediction
- **orchestrator #8** Capability Auto-Match Suggester
- **orchestrator #6** Fleet Roster Diff View
- **orchestrator #8** Cross-Agent Dependency Graph
- **researcher #1** Q4 context regression
- **researcher #3** No post-load functional probe / binding verify
- **researcher #4** Divergent parallel paths
- **builder #1** Component Library v1
- **builder #2** Goal Cycle Timeline Panel
- **builder #3** Fleet Health Dashboard
- **builder #7** Error Boundary + Fallback UI
- **archivist #4** Orphan Node Remediation
- **archivist #5** Retrieval Quality Benchmark
- **archivist #8** Knowledge Gap Detector
- **scribe #6** Synthesis Quality Score
- **designer #2** Information Density Pass
- **designer #3** Data Visualization Upgrade
- **designer #5** Notification System

## REAL claims (verified + artifact present)
- **orchestrator #1** Hot LLM Loading Functions - Expansion + Functional  -> `memory/orchestrator/model_scheduler.py`
- **orchestrator #2** Hotload Execute Engine (live)  -> `memory/ops/blockers.md`
- **orchestrator #3** Agent Activation State Machine  -> `memory/orchestrator/agent_state_machine.py`
- **orchestrator #9** Multi-Host Load Balancer  -> `memory/llm/hosts.md`
- **orchestrator #10** Hotload Regression Suite  -> `memory/orchestrator/hotload_regress.py`
- **orchestrator #1** Auto Goal-Cycle Transition  -> `memory/orchestrator/auto_cycle_transition.py`
- **orchestrator #2** Capacity Planner Panel  -> `memory/orchestrator/capacity-gauge-ui-2026-11-18.md`
- **orchestrator #3** One-Command Re-role  -> `memory/orchestrator/rerole-progress-2026-11-18.md`
- **orchestrator #4** Retirement Checklist Automation  -> `memory/orchestrator/retire-agent-built-2026-11-18.md`
- **orchestrator #5** Goal Slip Prediction API  -> `memory/goals/slip_prediction_table.json`
- **orchestrator #7** Onboarding Pack v3 Template  -> `memory/orchestrator/goal7-template-flag-evidence-2026-11-18.md`
- **orchestrator #9** Fleet Health Composite Score  -> `memory/orchestrator/health-composite-2026-11-18.md`
- **orchestrator #10** Cycle Narrative Auto-Generator  -> `memory/orchestrator/cycle_narrative.py`
- **researcher #2** Idle-wait deadlock  -> `memory/researcher/hot_load.py`
- **researcher #1** Unified Hot-Loader (`memory/researcher/hot_load.py`)  -> `memory/researcher/hot_load.py`
- **researcher #2** Q4 Context-Regression Test  -> `memory/llm/studio-api.md`
- **researcher #3** Post-Load Binding-Verify (residency matrix as automated check)  -> `memory/researcher/hot_load.py`
- **researcher #4** Eviction-Awareness Rule + Unit Test  -> `memory/researcher/test_eviction_restore.py`
- **researcher #5** Load-Trend Feed Integration  -> `memory/ops/load_trend.py`
- **researcher #6** Overnight-Unload Correlation  -> `memory/llm/overnight-unload.md`
- **researcher #7** FleetHotLoad Watchdog Spec (buildable handoff)  -> `memory/researcher/fleet-hotload-watchdog-spec.md`
- **researcher #8** Researcher SLA Tracker (cycle-6)  -> `memory/researcher/sla-report-cycle6.md`
- **builder #4** Uploads Panel v2  -> `memory/builder/uploads_v2_evidence_2026-11-18.md`
- **builder #5** Dark/Light Theme Toggle  -> `memory/builder/verify_theme_toggle_2026-11-17.md`
- **builder #6** Build-Verify-Pin Automation  -> `memory/builder/MEMORY.md`
- **builder #8** Mobile Responsive Pass  -> `memory/builder/mobile_hamburger_check.py`
- **builder #9** Keyboard Navigation  -> `memory/builder/kb_nav_evidence_2026-11-18.md`
- **builder #10** Portal Performance Budget  -> `memory/builder/perf_check.py`
- **archivist #1** Knowledge Graph Integrity Report  -> `memory/archivist/kg-report-cycle5.md`
- **archivist #2** Citation Accuracy Audit  -> `memory/archivist/citation-audit-cycle5-report.md`
- **archivist #3** Auto-Link Suggestion Engine  -> `memory/archivist/suggest_links.py`
- **archivist #6** KB Freshness Policy  -> `memory/archivist/freshness-policy.md`
- **archivist #7** Cross-Reference Integrity  -> `memory/archivist/xref-fix-log-2026-11-19.md`
- **archivist #9** Archivist API Endpoint  -> `memory/archivist/kb_search.py`
- **archivist #10** Weekly Digest Generator  -> `memory/archivist/weekly_digest.py`
- **scribe #1** Decision Log v2  -> `memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md`
- **scribe #2** Thread Compression Engine  -> `memory/scribe/compress.py`
- **scribe #3** Context Handoff Template  -> `memory/scribe/handoff-template.md`
- **scribe #4** Weekly Fleet Summary  -> `memory/scribe/weekly_summary.py`
- **scribe #5** Open Items Tracker  -> `memory/scribe/open-items.md`
- **scribe #7** Supersession Chain Validator  -> `memory/scribe/chain_check.py`
- **scribe #8** Agent Voice Consistency  -> `memory/scribe/attribution.py`
- **scribe #9** Pre-Meeting Brief Generator  -> `memory/scribe/meeting-brief-latest.md`
- **scribe #10** Memory Hygiene Report  -> `memory/scribe/memory-hygiene-2026-W47.md`
- **verifier #11** Hot LLM Load Functional Test Suite  -> `memory/verifier/goal11-hotload-progress-2026-11-18.md`
- **verifier #1** Smoke Test Suite v2  -> `memory/verifier/goal1-smoke8-evidence-2026-11-18.md`
- **verifier #2** Evidence Report Generator  -> `memory/verifier/gen_report.py`
- **verifier #3** Regression Guard  -> `memory/verifier/goal3-regression-guard-evidence-2026-11-18.md`
- **verifier #4** API Contract Tests  -> `memory/verifier/contract_test.py`
- **verifier #5** Evidence Freshness Audit  -> `memory/verifier/freshness_audit.py`
- **verifier #6** Concurrency Stress Test  -> `memory/verifier/goal6-concurrency-stress-evidence-2026-11-18.md`
- **verifier #7** UI Visual Regression  -> `memory/verifier/visual_regression.py`
- **verifier #8** Goal Closure Validator  -> `memory/verifier/closure_validate.py`
- **verifier #9** Portal Accessibility Audit  -> `memory/verifier/a11y-report.md`
- **verifier #10** Verification SLA Dashboard  -> `memory/verifier/css-tokenization-verify-2026-11-17.md`
- **designer #1** Design Token System  -> `memory/designer/apply_designer_scale_patch.py`
- **designer #4** Empty State Design  -> `memory/builder/empty_states_wire_2026-11-19.md`
- **designer #6** Loading Skeleton Screens  -> `memory/designer/skeleton-investigation-2026-11-19.md`
- **designer #7** Typography Hierarchy Audit  -> `memory/designer/goal7-typography-audit-2026-11-19.md`
- **designer #8** Icon System  -> `memory/builder/icons_js_created_2026-11-19.md`
- **designer #9** Portal Onboarding Tour  -> `memory/researcher/goal9-tour-stale-evidence-2026-11-19.md`
- **designer #10** Print-Ready Report Layout  -> `memory/orchestrator/designer-goal10-print-stale-overclaim-2026-11-19.md`
- **mechanic #1** Proactive Health Check Cron  -> `memory/mechanic/health_check.py`
- **mechanic #2** Auto-Restart Runbook  -> `memory/mechanic/auto_restart.py`
- **mechanic #3** Host Recovery Matrix  -> `memory/mechanic/recovery-matrix.md`
- **mechanic #4** Disk Space Monitor + Auto-Clean  -> `memory/mechanic/disk_monitor.py`
- **mechanic #5** Network Connectivity Probe  -> `memory/mechanic/net_probe.py`
- **mechanic #6** Portal Process Watchdog  -> `memory/mechanic/portal_watchdog.py`
- **mechanic #7** Log Rotation + Retention  -> `memory/mechanic/log_rotate.py`
- **mechanic #8** Fleet Status API  -> `memory/researcher/mechanic-goal8-fleet-status-stale-2026-11-19.md`
- **mechanic #9** Incident Post-Mortem Template  -> `memory/mechanic/postmortem_gen.py`
- **mechanic #10** Reboot Recovery Drill  -> `memory/mechanic/deploy_reboot_recovery_all.py`
