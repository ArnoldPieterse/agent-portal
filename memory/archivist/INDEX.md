# memory/archivist — pointer map
Last updated: 2026-11-14.

## Entries
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

## Linked content (KG orphan remediation 2026-11-19)
- [hostdoc_consistency_v2.py](memory/archivist/hostdoc_consistency_v2.py)
- [ingest.py](memory/archivist/ingest.py)
