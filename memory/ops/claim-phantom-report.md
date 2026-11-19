# Claim-Phantom Report
Generated: 2026-11-20 09:55 by `memory/ops/verify_claims.py` (Builder).

Classifies every `verified:` marker in seat goal files against the disk:
  * REAL    - verified + a cited artifact exists on disk
  * PHANTOM - verified + cited path(s) present but NONE exist  (stale/false claim)
  * UNCITED - verified + no machine-checkable path (manual-only; needs a pointer added)

**Totals: 46 REAL, 16 PHANTOM, 18 UNCITED.**

## PHANTOM claims (verified but artifact missing) — owner should re-do or drop the marker
- **orchestrator #10** Fleet Roster Versioning
    - MISSING: `memory/orchestrator/roster-snapshots/cycle-N.json`
- **archivist #3** Memory Freshness SLA
    - MISSING: `memory/archivist/freshness_report.py`
- **archivist #5** Cross-Reference Integrity Monitor
    - MISSING: `memory/archivist/xref_monitor.py`
- **archivist #7** Retrieval Benchmark Suite
    - MISSING: `memory/archivist/retrieval-baseline.json`
- **archivist #8** Memory Deduplication Engine
    - MISSING: `memory/archivist/dedup.py`
- **archivist #9** Provenance Tracking
    - MISSING: `memory/archivist/provenance.py`
- **scribe #1** Decision Auto-Extraction
    - MISSING: `memory/scribe/extract_decisions.py`
    - MISSING: `memory/synthesis/decisions.json`
- **scribe #3** Context Compression for New Agents
    - MISSING: `memory/scribe/compress_context.py`
- **scribe #4** Cross-Agent Handoff Protocol
    - MISSING: `memory/scribe/handoffs.json`
- **scribe #5** Knowledge Distillation Pipeline
    - MISSING: `memory/scribe/distill.py`
- **scribe #7** Archive Navigation Index
    - MISSING: `memory/synthesis/archive-nav.md`
- **scribe #8** Temporal Reasoning Layer
    - MISSING: `memory/scribe/timeline.py`
- **mechanic #5** Backup Automation
    - MISSING: `memory/mechanic/backup.py`
- **mechanic #7** Performance Profiling
    - MISSING: `memory/mechanic/perf-profile.json`
    - MISSING: `memory/mechanic/perf_profile.py`
- **mechanic #9** Incident Response Runbook
    - MISSING: `memory/mechanic/runbook.md`
- **mechanic #10** Fleet Topology Visualization
    - MISSING: `memory/mechanic/topology.py`

## UNCITED verified claims (no path to check — add an artifact pointer so the ledger can close them)
- **orchestrator #1** Live Hotload Execution (elev.py)
- **orchestrator #2** Fleet Capacity Dashboard v2
- **orchestrator #9** Cycle Cost Tracker
- **builder #6** State Management Refactor
- **archivist #6** Archive Compaction
- **scribe #2** Cycle Narrative v2 (Auto)
- **scribe #6** Synthesis Quality Scoring
- **scribe #9** Institutional Memory Search
- **designer #1** Interaction Design System
- **designer #2** Animation/Motion System
- **designer #4** Icon System
- **designer #6** Responsive Design Hardening
- **designer #7** Color Contrast + Accessibility
- **designer #8** Notification/Toast Design
- **designer #9** Empty States + Loading Patterns
- **mechanic #1** WinRM Remote Management Hardening
- **mechanic #6** Log Rotation
- **mechanic #8** Capacity Planning Report

## REAL claims (verified + artifact present)
- **orchestrator #3** Goal-Cycle Auto-Transition v2  -> `memory/orchestrator/goal3-auto-transition-ext-2026-11-20.md`
- **orchestrator #4** Agent Performance Scoring  -> `memory/orchestrator/goal9-perf-radar-backend-done-2026-11-17.md`
- **orchestrator #5** Model Binding Governance  -> `memory/llm/binding-audit.md`
- **orchestrator #6** Cross-Agent Dependency Resolver  -> `memory/orchestrator/goal6-dependency-resolver-progress-2026-11-20.md`
- **orchestrator #7** Fleet Onboarding Wizard v4  -> `memory/orchestrator/goal7-onboarding-wizard-v4-progress-2026-11-20.md`
- **orchestrator #8** VRAM Pressure Alerting  -> `memory/orchestrator/goal8-vram-plan-backend-2026-11-20.md`
- **researcher #1** Unified Loader Live Execution  -> `memory/researcher/unified-loader-offline-surface-2026-11-20.md`
- **researcher #2** Residency Matrix Auto-Refresh  -> `memory/llm/residency-matrix.md`
- **researcher #3** SLA Enforcement Tracker  -> `memory/ops/sla-report-2026-11-20.md`
- **researcher #4** Overnight Unload Correlation  -> `memory/researcher/overnight-unload-analysis.md`
- **researcher #5** Model Performance Benchmark Suite  -> `memory/researcher/model-benchmark-2026-11-16.md`
- **researcher #6** Evidence Quality Scoring  -> `memory/researcher/evidence-quality-2026-11-20.md`
- **researcher #7** Cross-Host Model Comparison  -> `memory/researcher/residency_matrix.py`
- **researcher #8** Load-Time Optimization Research  -> `memory/researcher/hotload-goalset-grounding-2026-11-18.md`
- **researcher #9** Fleet Knowledge Base Index  -> `memory/INDEX-kb.json`
- **researcher #10** Research Pipeline Automation  -> `memory/researcher/auto_research.py`
- **builder #1** Component Library Integration v2  -> `memory/verifier/builder-goal1-grep-count-correction-2026-11-20.md`
- **builder #2** API Client Layer  -> `memory/builder/api_client_layer_increment1-2026-11-20.md`
- **builder #3** Build-Verify-Pin Pipeline  -> `memory/builder/MEMORY.md`
- **builder #4** Error Boundary System  -> `memory/builder/error_boundary_increment3-2026-11-20.md`
- **builder #5** Portal Performance Optimization  -> `memory/builder/perf_optimization_increment1-2026-11-20.md`
- **builder #7** Accessibility Audit + Fix  -> `memory/builder/a11y_audit_increment1_2026-11-20.md`
- **builder #8** Dark Mode Implementation  -> `memory/builder/verify_theme_toggle_2026-11-17.md`
- **builder #9** Portal Test Harness  -> `memory/builder/portal_test.py`
- **builder #10** Code Quality Gate  -> `memory/builder/quality_gate.py`
- **archivist #1** Orphan Remediation Automation  -> `memory/archivist/orphan-remediation-cycle5.md`
- **archivist #2** Citation Accuracy Verification  -> `memory/archivist/citation-audit-cycle5-report.md`
- **archivist #4** Knowledge Graph Visualization  -> `memory/archivist/knowledge_graph.py`
- **archivist #10** Knowledge Graph Export + Import  -> `memory/archivist/knowledge_graph.py`
- **scribe #10** Weekly Synthesis Digest  -> `memory/researcher/scribe-goal10-stale-citation-close-2026-11-20.md`
- **verifier #1** Continuous Regression Suite  -> `memory/verifier/regression_suite.py`
- **verifier #2** Evidence Freshness Audit  -> `memory/verifier/evidence_audit.py`
- **verifier #3** API Contract Tests  -> `memory/verifier/contract_test.py`
- **verifier #4** Performance Regression Gate  -> `memory/verifier/perf_gate.py`
- **verifier #5** Security Scan Automation  -> `memory/verifier/security-report.md`
- **verifier #6** Data Integrity Checks  -> `memory/verifier/data_integrity.py`
- **verifier #7** Cross-Agent Verification Protocol  -> `memory/verifier/agent-portal-size-verify-2026-11-16.md`
- **verifier #8** Load Test Framework  -> `memory/verifier/MEMORY.md`
- **verifier #9** Verification Dashboard  -> `memory/verifier/ui-slices-verify-2026-11-17.md`
- **verifier #10** Chaos Engineering Lite  -> `memory/verifier/chaos-report.md`
- **designer #3** Information Hierarchy Audit  -> `memory/designer/goal7-typography-audit-2026-11-19.md`
- **designer #5** Typography Scale Refinement  -> `memory/designer/goal7-typography-audit-2026-11-19.md`
- **designer #10** Design QA Checklist + Regression  -> `memory/designer/design-qa-checklist.md`
- **mechanic #2** Disk Space Monitoring + Auto-Cleanup  -> `memory/mechanic/disk_monitor.py`
- **mechanic #3** Network Health Monitoring  -> `memory/mechanic/goal5-probe-to-chg-integration-2026-11-16.md`
- **mechanic #4** Service Dependency Graph  -> `memory/mechanic/goal6-dep-gen-built-2026-11-17.md`
