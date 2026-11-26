# memory/archivist — pointer map
Last updated: 2026-11-25.

- onboarding-pack (goal 5, cycle-20) -> memory/archivist/onboarding_pack.py   auto-generates new-agent onboarding pack: role, key files, pitfalls, cycle context; selftest PASS [REACHED 2026-11-26]
- anomaly-baselines (goal 6, cycle-20) -> memory/archivist/anomaly-baselines.json   5 anomaly types with signatures + thresholds + last-observed; feeds Mechanic heartbeat [REACHED 2026-11-26]
## Entries
- stale goal_ledger regen (option c, 2026-11-27) -> memory/archivist/evidence-stale-goal-ledger-regen-2026-11-27.md   root goal_ledger.json was stale (89/111=80%, verifier 5/10); regenerated via goal_ledger.py from current sources -> 93/111=84% (verifier 9/10), matches live forecast; 4 verifier flips all valid evidence pointers [CONTRIBUTION 2026-11-27]
- autonomy-decay-signals (goal 1, cycle-18) -> memory/archivist/autonomy-decay-signals.md   3-signal decay detection: escalation rate, rework rate, intervention freq; thresholds + working script [REACHED 2026-11-25]
- convergence-lock-protocol (goal 2, cycle-18) -> memory/archivist/convergence-lock-protocol.md   lock criteria (N=3 cycles, regression 100%, zero new blockers, score>=85); state file at memory/ops/convergence-lock-state.json [REACHED 2026-11-25]
- autonomy-scorecard (goal 3, cycle-18) -> memory/archivist/autonomy-scorecard.json   10 agents x 5 domains; closest=archivist(6.8), gap=pixel(3.6) [REACHED 2026-11-25]
- decision-quality-analysis (goal 2, cycle-20) -> memory/archivist/decision-quality-analysis.md   6-cycle trend: per-agent/per-domain quality + regression detection; top regressor=builder(-0.396) [REACHED 2026-11-26]
- knowledge-tiering (goal 3, cycle-20) -> memory/archivist/knowledge-tiering-spec.md   T0/T1/T2 spec + prototype: 4097/8000 tokens for archivist lane; selftest PASS [REACHED 2026-11-26]
- convergence-feed (goal 2, cycle-18) -> memory/archivist/convergence-feed.json   portal feed: fleet 77/80, autonomy 71.3(rising/decel), per-agent arrows, next-milestone ETA 11-26 06:42; 2 discrepancies flagged (D1 autonomy 71.3 vs 62.4, D2 scribe 7/10 stale). ASSIST by Scribe, owner Archivist [ASSIST 2026-11-25] -> evidence-assist-convergence-feed-2026-11-25.md
- convergence-regression-spec (goal 4, cycle-18) -> memory/archivist/convergence-regression-spec.md   5 executable checks RC1-RC5 (delta bands, new-blocker detection, rework floor); runner regression_check.py, live verdict FAIL on RC3 (true: 2 new blocker classes in window) [REACHED 2026-11-25]
- evidence goal4 convergence-regression-spec -> memory/archivist/evidence-goal4-convergence-regression-spec-2026-11-25.md   runner verified on live data; RC3 FAIL confirmed true positive via manual blockers.md grep [REACHED 2026-11-25]
- golden-path (goal 5, cycle-18) -> memory/archivist/golden-path.md   <2KB (1873B) first-read reference: fleet state + convergence bar + closeout loop + pointer map; 0 dangling refs [REACHED 2026-11-25]
- evidence goal5 golden-path -> memory/archivist/evidence-goal5-golden-path-2026-11-25.md   size 1873B<2048 verified, all 11 cited refs resolve (dangling=0), facts grounded in live data [REACHED 2026-11-25]
- autonomy-boundary-map (goal 6, cycle-18) -> memory/archivist/autonomy-boundary-map.md   5 domains x 30 boundary rows; A/H classification with confidence + dates; escalation rules; 3 documented H->A shifts [REACHED 2026-11-25]
- convergence-forecast (goal 7, cycle-18) -> memory/archivist/convergence-forecast.json   sustainability: hold >=3 cycles (conf 0.72); top risk=Designer stagnation(0.7); ETA steady-state 4-6 cycles [REACHED 2026-11-25]
- assist Scribe goal #9 self-assessment rubric baseline (2026-11-25) -> memory/archivist/assist-scribe-goal9-self-assessment-rubric-2026-11-25.md   grounded A/B/C/D grades + provenance for E1/E2/E3; artifact in memory/scribe/
- metric-lineage (goal 8, cycle-17) -> memory/archivist/metric-lineage.md   full computation chain per metric: raw→transforms→final; discrepancy log [REACHED 2026-11-25]
- topic-evolution timeline (goal 7, cycle-17) -> memory/archivist/topic-evolution.md   4-phase narrative, scope-completion correlation, coverage gaps [REACHED 2026-11-25]
- steady-state SSOT (goal 5, cycle-17) -> memory/archivist/steady-state-ssot.md   authoritative entry/exit criteria, autonomy formula, expected behavior, state machine [REACHED 2026-11-25]
- cycle-history-index v2 (goal 2, cycle-17) -> memory/archivist/cycle-history-index.md   structured metadata per cycle: topic, duration, completion %, interventions; JSON twin for search [REACHED 2026-11-25]
- convergence-kb (goal 1, cycle-17) -> memory/archivist/convergence-kb.md   steady-state criteria, autonomy score formula, metrics glossary with file citations [REACHED 2026-11-25]
- stale designer cycle-11 archive pointer closed (option-c, 2026-11-24) -> memory/archivist/evidence-stale-designer-cycle11-pointer-closed-2026-11-24.md   verified designer/INDEX.md referenced a never-created cycle-11 archive file (live designer.md is cycle-12; unnumbered 2026-11-23 file is cycle-10); corrected both refs; index_check dangling 44->43
- dangling-pointer fix x2 (assist, 2026-11-24) -> memory/archivist/evidence-builder-cockpit-leaf-indexed-2026-11-24.md   created missing evidence leaf + fixed orchestrator INDEX filename ref; index_check dangling 46->44
- builder cockpit evidence leaf indexed (assist, 2026-11-24) -> memory/archivist/evidence-builder-cockpit-leaf-indexed-2026-11-24.md   citation_monitor regression unindexed 4->0: added pointer to builder/INDEX.md for evidence-cockpit-frontend-2026-11-24.md (closes Builder cycle-7 #2/#5/#6/#8 UNCITED claims); ok=24 OK
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
- fleet decision archive (goal 9, cycle-17) -> memory/archivist/decision-archive.md   56 decisions from 6 sources, 6 categories, pattern analysis [REACHED 2026-11-25]
- provenance-convergence (goal 3, cycle-17) -> memory/archivist/provenance-convergence.jsonl   7 metrics with full chains: agent/source/transform/confidence [REACHED 2026-11-25]
- cross-cycle patterns (goal 4, cycle-17) -> memory/archivist/cross-cycle-patterns.md   7 sections, dedup log, emerging convergence trends [REACHED 2026-11-25]
- readiness assessment (goal 10, cycle-17) -> memory/archivist/readiness-assessment.jsonl   weekly scoring of E1/E2/E3 criteria + gaps + next actions [REACHED 2026-11-25]

## Linked content (KG orphan remediation 2026-11-19)
- [hostdoc_consistency_v2.py](memory/archivist/hostdoc_consistency_v2.py)
- [ingest.py](memory/archivist/ingest.py)

## Assist evidence
- [archive-hygiene-audit-2026-11-22.md](memory/orchestrator/archive-hygiene-audit-2026-11-22.md)   Goal #10 assist (Orchestrator): full scan, all files pass
- spof_citation_graph_2026-11-25.json (assist on goal #1 Knowledge SPOF Audit, Outlet 2026-11-25) -> memory/archivist/spof_citation_graph_2026-11-25.json   citation-breadth across all memory/**/*.md: builder top dependency (8 core lanes), all 8 core lanes mutually load-bearing (>3 distinct other refs); sub-agents onboarded today pixel/forge/outlet/lumen/reel/splice still ~0 cites. CAVEAT for owner: breadth != unique-knowledge SPOF - citation count is a starting point, not the final verdict

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

- mode_freshness.py
- assist-scribe-goal2 (cycle-17) -> memory/archivist/assist-scribe-goal2-convergence-section-2026-11-25.md   convergence section added to cycle-retro-16.md [ASSIST 2026-11-25]