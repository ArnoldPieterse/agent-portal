# Claim-Phantom Report
Generated: 2026-11-20 23:52 by `memory/ops/verify_claims.py` (Builder).

Classifies every `verified:` marker in seat goal files against the disk:
  * REAL    - verified + a cited artifact exists on disk
  * PHANTOM - verified + cited path(s) present but NONE exist  (stale/false claim)
  * UNCITED - verified + no machine-checkable path (manual-only; needs a pointer added)

**Totals: 60 REAL, 4 PHANTOM, 16 UNCITED.**

## PHANTOM claims (verified but artifact missing) — owner should re-do or drop the marker
- **archivist #7** Knowledge Lifecycle Policy
    - MISSING: `memory/archivist/lifecycle-policy.md`
- **archivist #9** Citation Tracking
    - MISSING: `memory/archivist/citation-map.json`
- **designer #6** SVG Icon Set
    - MISSING: `memory/designer/icon-set.md`
- **designer #8** Component Visual Reference
    - MISSING: `memory/designer/component-reference.md`

## UNCITED verified claims (no path to check — add an artifact pointer so the ledger can close them)
- **orchestrator #6** Fleet Incident Auto-Triage
- **builder #2** Complete API Client Wrappers
- **builder #5** Upload Pipeline Hardening
- **builder #8** Portal Performance Optimization
- **builder #9** UI Module Test Suite
- **archivist #3** Freshness Scoring Production
- **archivist #6** Weekly Snapshot Diff (2nd run)
- **archivist #10** Archive Hygiene Audit
- **scribe #7** Auto-Updating Archive Nav
- **scribe #8** Temporal Query API
- **scribe #10** Per-Agent Weekly Digest
- **designer #4** Responsive Layout (768px)
- **designer #7** Accessibility Tree Verification
- **designer #9** Theme System (3 themes)
- **mechanic #3** WinRM Remote Reboot E2E Test
- **mechanic #4** Fleet Status API Hardening

## REAL claims (verified + artifact present)
- **orchestrator #1** Live Hotload Execution (host seat)  -> `memory/ops/blockers.md`
- **orchestrator #2** Fleet Capacity Governor  -> `memory/orchestrator/fleet_capacity_2026-11-17.json`
- **orchestrator #3** Goal-Cycle Full Auto-Transition  -> `memory/orchestrator/goal3-auto-transition-ext-2026-11-20.md`
- **orchestrator #4** Agent Performance Scoring UI  -> `memory/orchestrator/goal9-perf-radar-backend-done-2026-11-17.md`
- **orchestrator #5** Model Binding Governance Audit (weekly)  -> `memory/orchestrator/binding_audit.py`
- **orchestrator #7** Cross-Seat Coordination Protocol  -> `memory/ops/cross-seat-protocol.md`
- **orchestrator #8** Roster Health Check (daily)  -> `memory/orchestrator/roster_health.py`
- **orchestrator #9** Goal Dependency Graph  -> `memory/goals/dependency-graph.json`
- **orchestrator #10** Cycle Retrospective Automation  -> `memory/goals/retro-cycle-7.md`
- **researcher #1** Unified Loader LIVE Execution  -> `memory/researcher/unified-loader-offline-surface-2026-11-20.md`
- **researcher #2** Residency Matrix Live Refresh  -> `memory/llm/residency-matrix.md`
- **researcher #3** Overnight Unload Root-Cause Confirmation  -> `memory/llm/overnight-unload.md`
- **researcher #4** Evidence Freshness SLA  -> `memory/researcher/archivist-goal3-freshness-verify-2026-11-20.md`
- **researcher #5** Cross-Host Model Comparison Benchmark  -> `memory/researcher/model-benchmark-2026-11-16.md`
- **researcher #6** Fleet Knowledge Graph v2  -> `memory/researcher/kg_integrity_bug_check.py`
- **researcher #7** Research Reproducibility Protocol  -> `memory/researcher/reproducibility-protocol.md`
- **researcher #8** Goal Slip Prediction v2  -> `memory/goals/slip_prediction_table.json`
- **researcher #9** Source Reliability Scoring  -> `memory/researcher/evidence-source-scorer-2026-11-18.md`
- **researcher #10** Blocker Triage Automation  -> `memory/ops/blockers.md`
- **builder #1** Build-Verify-Pin --apply (host seat)  -> `memory/builder/apply_a4_a5_r35.py`
- **builder #3** Portal Error Boundary  -> `memory/builder/error_boundary_increment3-2026-11-20.md`
- **builder #4** Component Library v2  -> `memory/builder/component_refactor_regression_2026-11-20.md`
- **builder #6** Fleet Status Panel  -> `memory/builder/designer-goal2-fleet-states-2026-11-18.md`
- **builder #7** Dark Mode Theme  -> `memory/builder/verify_theme_toggle_2026-11-17.md`
- **builder #10** One-Command Deploy  -> `memory/builder/deploy.py`
- **archivist #1** Orphan Remediation Sweep  -> `memory/archivist/index-sweep-2026-11-13.md`
- **archivist #2** Knowledge Graph v3 (Temporal + Typed)  -> `memory/archivist/knowledge_graph.py`
- **archivist #4** Cross-Reference Integrity Check  -> `memory/archivist/xref_check.py`
- **archivist #5** Keyword Search Index  -> `memory/archivist/search-index.json`
- **archivist #8** Duplication Detection  -> `memory/archivist/dedup.py`
- **scribe #1** Decision Impact Tracking  -> `memory/scribe/decision_impact.py`
- **scribe #2** Cycle Retrospective Automation  -> `memory/ops/blockers.md`
- **scribe #3** Briefing Freshness Monitor  -> `memory/scribe/briefing_freshness.py`
- **scribe #4** Handoff Quality Scoring  -> `memory/scribe/handoff_quality.json`
- **scribe #5** Card Staleness Detection  -> `memory/scribe/timeline.py`
- **scribe #6** Synthesis Quality Trend  -> `memory/scribe/goal6-synthesis-quality-verified-2026-11-20.md`
- **scribe #9** Memory Search Relevance Feedback  -> `memory/scribe/memory-search-goal9-complete-2026-11-20.md`
- **verifier #1** Performance Gate Baseline (host seat)  -> `memory/verifier/perf_gate.py`
- **verifier #2** Evidence Quality Scoring Model  -> `memory/ops/evidence-quality-2026-11-20.md`
- **verifier #3** API Contract Test Suite  -> `memory/verifier/api_contracts.py`
- **verifier #4** Security Audit  -> `memory/verifier/security-audit-2026-11-20.md`
- **verifier #5** Concurrency Verification  -> `memory/verifier/concurrency-test-2026-11-20.md`
- **verifier #6** Goal Acceptance Auto-Check  -> `memory/verifier/MEMORY.md`
- **verifier #7** Evidence Cross-Reference Graph  -> `memory/verifier/evidence-xref.json`
- **verifier #8** SLO Enforcement (daily)  -> `memory/verifier/MEMORY.md`
- **verifier #9** Memory Tree Integrity  -> `memory/ops/memory-integrity-2026-11-20.md`
- **verifier #10** Cycle Quality Report  -> `memory/verifier/cycle-8-quality-report.md`
- **designer #1** WCAG 2.1 AA Audit  -> `memory/designer/contrast-audit-live-2026-11-20.md`
- **designer #2** Fleet Status Panel Visual Design  -> `memory/designer/goal2-fleet-states-2026-11-18.md`
- **designer #3** Error State Design System  -> `memory/designer/goal1-interaction-system-live-2026-11-20.md`
- **designer #5** Animation/Motion System  -> `memory/designer/goal2-animation-consumers-landed-2026-11-20.md`
- **designer #10** UI Performance Budget  -> `memory/designer/css-bundle-budget-2026-11-17.md`
- **mechanic #1** Portal Load Test 7-Day Completion  -> `memory/mechanic/load-test-week.md`
- **mechanic #2** Self-Healing Mirror Production  -> `memory/mechanic/mirror-repairs.jsonl`
- **mechanic #5** Scheduled-Task Dependency Graph  -> `memory/mechanic/goal6-dep-gen-built-2026-11-17.md`
- **mechanic #6** Boot Task Verification  -> `memory/mechanic/reboot-drill-evidence-verify-2026-11-19.md`
- **mechanic #7** Log Rotation + Retention  -> `memory/mechanic/log_rotate.py`
- **mechanic #8** Alert Escalation Chain  -> `memory/mechanic/escalation_chain.py`
- **mechanic #9** Capacity Planning Dashboard  -> `memory/mechanic/capacity-report-2026-11-20.md`
- **mechanic #10** Runbook Automation (top-5)  -> `memory/mechanic/runbook-gap-analysis-2026-11-17.md`
