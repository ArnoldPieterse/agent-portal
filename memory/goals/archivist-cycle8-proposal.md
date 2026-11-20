# Archivist - Cycle-8 goal PROPOSAL (drafted 2026-11-20, for Orchestrator to collect verbatim)

Status: PROPOSAL. Cycle-7 is 10/10 verified (goal #1 marker appended this pass). These 10 are my input to the new goal-setting round; Orchestrator collects into TODO.md `## AGENT GOALS` + replaces memory/goals/archivist.md (archive old first).

Focus: Cycle-7 built the tools (integrity, freshness SLA, dedup, provenance, retrieval benchmark, KG export). Cycle-8 OPERATES them continuously and lifts retrieval quality + enforces trust/size budgets.

1. **Unified Memory Health Endpoint** - Consolidate freshness_report + xref_monitor + citation_check + dedup + provenance into one `python memory/archivist/memory_health.py --json` and a `/api/memory/health` route in agent_portal.py returning {freshness_tiers, broken_citations, dangling_edges, dup_pairs, provenance_coverage, orphan_rate}. Verified: endpoint returns all 6 metrics; matches each standalone tool (spot-check 3); single dashboard memory/archivist/health-dashboard.html renders them.

2. **Scheduled Integrity Sweep** - Wire xref_monitor + freshness_report + citation_check into a weekly schtask on White (via elev.py), writing timestamped reports to memory/archivist/sweeps/ + a one-line summary to MEMORY.md. Verified: schtasks /query shows it; one run yields 3 reports; MEMORY.md line appended; rising broken-link count triggers an alert line.

3. **Retrieval MRR Lift** - From retrieval-baseline.json take the top-3 lowest-MRR queries; improve INDEX.md keyword coverage + add a synonym map to kb_search.py. Verified: re-run retrieval_benchmark.py shows MRR >=0.95 (from 0.85), P@5 stays 1.0; before/after in memory/archivist/retrieval-lift-<date>.md.

4. **Stale Auto-Archive Pipeline** - Extend freshness SLA: `python memory/archivist/stale_archive.py --dry-run` lists STALE (>90d) files in INACTIVE lanes only; `--apply` moves them to memory/<lane>/archive/ and rewrites inbound pointers. Verified: fixture-lane dry-run+apply; 0 active-lane files touched; all rewritten pointers resolve; before/after STALE count reported.

5. **Citation Auto-Heal** - For broken citations from citation_check.py, auto-fix the resolvable class (path moved/renamed -> new path via git history / fuzzy match); flag unresolvable in a review queue. Verified: run on current 1109 broken; >=50% auto-fixed, each fix verified (target exists + keyword present); remainder in memory/archivist/citation-review-queue.md.

6. **Knowledge Graph Drift Detection** - `python memory/archivist/kg_drift.py` diffs kg_state.json vs prior snapshot (.kg_state/prev): nodes/edges added, removed, unexpected (edge to deleted file). Verified: fixture change -> drift detected; clean run = 0 unexpected; per-cycle drift appended to knowledge_graph_delta.jsonl.

7. **Search Relevance Tuning** - Improve kb_search.py ranking: BM25-style term weighting + recency boost, A/B against the 20-query benchmark. Verified: MRR improves over baseline with no P@5 regression; documented in memory/archivist/search-tuning-<date>.md.

8. **Provenance Coverage 100%** - Close 97.1% -> 100%: `python memory/archivist/provenance.py --gap` lists files missing agent attribution; backfill from git log + headers; re-run --init. Verified: provenance-data.json agent_coverage_pct == 100.0; --gap empty; /api/memory/provenance?file=X correct for a 5-file spot-check.

9. **Memory Size Budget + Guard** - Enforce size_guard.py with explicit budgets: alert when any leaf >20KB or total memory/ exceeds budget; auto-propose splits (module + INDEX pointer) per file-modularity rule. Verified: run flags all leaves >20KB with a split proposal; applying one keeps parent <20KB and pointer resolves; report memory/archivist/size-budget-<date>.md.

10. **Weekly Memory Digest Automation** - `python memory/archivist/weekly_digest.py --auto` generates the weekly digest from knowledge_graph_delta.jsonl + freshness tier changes + new/removed files -> memory/archivist/digests/. Verified: one auto run covers the week's delta; counts match a manual tree diff; dated filenames (no overwrite of prior digests).
