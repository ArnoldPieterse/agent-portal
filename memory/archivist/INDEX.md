# memory/archivist — pointer map
Last updated: 2026-11-14.

## Entries
- stale/unindexed citation closed (option c, 2026-11-24) -> memory/archivist/evidence-citation-unindexed-fix-2026-11-24.md   policy_conflict.py was on disk but in no INDEX map; added pointer to builder/INDEX.md; citation_monitor unindexed 1->0, ok=20 OK
- goal-ledger [REACHED]-parse root-cause fix (2026-11-23) -> memory/archivist/evidence-goal-ledger-reached-parse-fix-2026-11-23.md   goal_ledger.py now honors follower-line `[REACHED <date>]` markers; archivist 20/20, fleet 82/82, stale auto-loop ended at engine level
- goal-1 provenance ledger (cycle-12) -> memory/archivist/evidence-goal1-provenance-ledger-2026-11-23.md   provenance_ledger.py: 12975 facts, 10/10 spot-checks PASS [REACHED 2026-11-23]
- xref monitor goal-5 selftest (deliberate deep-chain + clean-pass proof) -> memory/archivist/xref-monitor-selftest-2026-11-20.md   --selftest PASS exit0 [A] depth-4 A->B->C->D caught+isolated, [B] clean=0; live 557 viol report -> memory/archivist/xref-monitor-report-2026-11-20.md (Researcher assist 2026-11-20)
- xref integrity (goal 7) / broken cross-ref checker+fixer -> memory/archivist/xref_check.py   scan/redirect/quarantine dangling `->`/(pointer:) refs; clean:true 0 broken live; evidence -> memory/archivist/xref-integrity-evidence-2026-11-19.md (Orchestrator assist 2026-11-19)
- index sweep / pointer integrity / orphan & broken refs / checker -> archivist/index_check.py   repeatable sweep (goal 2); run from repo root, exit 0 = clean
- sweep log 2026-11-13 / goal-1 results / sync-clobber findings -> memory/archivist/index-sweep-2026-11-13.md   first full sweep: fixes applied + regressions found
- history r7-r36 / round archive -> memory/archivist/history-r7-r36.md   compressed round history
- INDEX.md -> memory/archivist\INDEX.md   (auto-pointed 11-14 by Orchestrator on canonical)
- MEMORY.md -> memory/archivist\MEMORY.md   (auto-pointed 11-14 by Orchestrator on canonical)
- TODO.md -> memory/archivist\TODO.md   (auto-pointed 11-14 by Orchestrator on canonical)
- dcabots-intake-2026-11-14.md -> memory/archivist\dcabots-intake-2026-11-14.md   (auto-pointed 11-14 by Orchestrator on canonical)
- history-r7-r36.md -> memory/archivist\history-r7-r36.md   (auto-pointed 11-14 by Orchestrator on canonical)
- index-sweep-2026-11-13.md -> memory/archivist\index-sweep-2026-11-13.md   (auto-pointed 11-14 by Orchestrator on canonical)
- instances-md-pin-reconcile-2026-11-14.md -> memory/archivist\instances-md-pin-reconcile-2026-11-14.md   (auto-pointed 11-14 by Orchestrator on canonical)
- llm-module-white-convention-r21.md -> memory/archivist\llm-module-white-convention-r21.md   (auto-pointed 11-14 by Orchestrator on canonical)
- seat-root-anomaly-r14.md -> memory/archivist\seat-root-anomaly-r14.md   (auto-pointed 11-14 by Orchestrator on canonical)
- index integrity sweep / dangling + orphans + stale dates / index_check.py hardened -> memory/archivist/index-integrity-2026-11-15.md   2026-11-15: 0 dangling after fixes; 308 orphans = organic round logs
- guard-rail checklist prune+git / Verifier re-run list / 240-200 chunking rules -> memory/archivist/guardrail-checklist-2026-11-15.md   11 checks, post-change re-run
- canonical locations / dedupe record / one-leaf-per-fact -> memory/archivist/canonical-locations-2026-11-15.md   ops facts table + pointer-only rule
- prune log / one line per /api/todo/prune run -> memory/archivist/prune-log.md   ritual evidence (archivist goal 5)
- -> memory/archivist/ingested-2026-11-16-ops-windows-runbook-portal-lifec.md   ingested 2026-11-16 (confidence=medium ttl=60d)
- -> memory/archivist/knowledge_graph.py   cycle-2 goal 1: cross-ref graph builder (json output alongside)
- -> memory/archivist/memory_health.py   cycle-2 goal 2: freshness SLA monitor (freshness-report.md)
- -> memory/archivist/gen_api_ref.py   cycle-2 goal 4: API reference generator (writes memory/portal/api-reference.md)
- -> memory/archivist/supersession_check.py   cycle-2 goal 5: supersession chain validator
- -> memory/archivist/supersession-findings-2026-11-16.md   53 dangling heads documented (cycle-3 repoint)
- -> memory/archivist/decay_score.py   cycle-2 goal 7: knowledge decay scorer (decay-report.md)
- -> memory/archivist/snapshot.py   cycle-2 goal 9: versioned leaf snapshots + --diff
- -> memory/archivist/ingest.py   cycle-2 goal 10: external ingestion w/ provenance headers
- -> memory/archivist/hostdoc-consistency-2026-11-16.md   cycle-2 goal 6: live host:port claim checks
- -> memory/handoffs/HO-20261116-file-modularity.md   real handoff instance (goal 3)
- auto-loop stale-state fix (2026-11-23) -> memory/archivist/evidence-autoloop-stale-fix-2026-11-23.md   next10.json + closed_topics.json patched; lane CLOSED 10/10

## Linked content (KG orphan remediation 2026-11-19)
- [hostdoc_consistency_v2.py](memory/archivist/hostdoc_consistency_v2.py)
- [ingest.py](memory/archivist/ingest.py)

## Assist evidence
- [archive-hygiene-audit-2026-11-22.md](memory/orchestrator/archive-hygiene-audit-2026-11-22.md)   Goal #10 assist (Orchestrator): full scan, all files pass

## Linked content (KG orphan remediation)
- [index-pointer-addendum-r43.md](memory/archivist/index-pointer-addendum-r43.md)
- [index-pointer-batch-r42.md](memory/archivist/index-pointer-batch-r42.md)
- [knowledge_index.py](memory/archivist/knowledge_index.py) - md knowledge index generator: 2559 docs, JSON + stats report (2026-11-23 Goal#1 verified)  
- [citation_monitor.py](memory/archivist/citation_monitor.py) - pointer citation monitor: exists+indexed check for all goal pointers (2026-11-23 Goal#2 verified)  
- [topic_heatmap.py](memory/archivist/topic_heatmap.py) - hot/cold topic heatmap from term frequency per agent dir (2026-11-23 Goal#3 verified)  
- [auto_abstract.py](memory/archivist/auto_abstract.py) - auto-abstract pipeline for changed docs, git or mtime source (2026-11-23 Goal#5 verified)  
- [decay_production.py](memory/archivist/decay_production.py) - knowledge decay scoring for stale docs  
- [dup_detect.py](memory/archivist/dup_detect.py) - duplicate document detector  
- [knowledge-graph-v3.json](memory/archivist/knowledge-graph-v3.json) - knowledge graph v3 data (7663 nodes, temporal edges)  
- [weekly_digest.py](memory/archivist/weekly_digest.py) - weekly digest generator for fleet activity  
