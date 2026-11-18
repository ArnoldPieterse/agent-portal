# Archivist - 10 goals (set 2026-11-18, cycle-5)

Focus: Knowledge graph quality + retrieval accuracy. Make the fleet's memory not just searchable but trustworthy: citation accuracy, orphan detection, and automated freshness maintenance.

1. **Knowledge Graph Integrity Report** - `python memory/archivist/kg_integrity.py` produces: total nodes, edge count, orphan count (no inbound edges), dangling reference count, cycle detection. Writes to memory/archivist/kg-report-cycle5.md. Verified: report exists with all 5 metrics; orphan count matches manual spot-check. (pointer: memory/archivist/knowledge_graph.py)

2. **Citation Accuracy Audit** - For 50 random KB entries, verify the cited source actually supports the claim (fetch URL, check content). Log pass/fail + confidence adjustment. Target: >90% accuracy. Verified: audit file exists with 50 entries scored; accuracy % reported.

3. **Auto-Link Suggestion Engine** - For each new KB entry, find 3 most-related existing entries (by shared terms + co-citation) and suggest link creation. `python memory/archivist/suggest_links.py --entry <id>`. Verified: suggestions for 5 test entries are topically relevant; no self-links or duplicates.

4. **Orphan Node Remediation** - For each orphan node found in goal #1, either: (a) create a link from a related entry, or (b) mark as intentionally standalone with reason. Target: <5% orphans after remediation. Verified: post-remediation run shows reduced orphan count; each action logged.

5. **Retrieval Quality Benchmark** - Define 20 test queries with known correct answers from the KB. Measure: precision@5, recall@10, MRR for the current retrieval method. Baseline established. Verified: benchmark script runs; metrics file exists with all 3 scores + per-query breakdown.

6. **KB Freshness Policy** - Define TTL per entry type (fact=90d, opinion=30d, procedure=180d). `python memory/archivist/freshness_sweep.py` flags expired entries for review. Verified: policy documented in memory/archivist/freshness-policy.md; script correctly flags test-expired entries.

7. **Cross-Reference Integrity** - Every "see also" or "related to" link in the KB must resolve to an existing entry. `python memory/archivist/xref_check.py` finds broken cross-refs and auto-fixes (remove or redirect). Verified: script runs; 0 broken xrefs remain after fix; log of fixes written.

8. **Knowledge Gap Detector** - Analyze goal files + chat logs for recurring topics that have NO corresponding KB entry. Generate a "knowledge gap" list with suggested entry titles. Verified: gap report exists; >=5 gaps identified; each has a suggested title + source to research.

9. **Archivist API Endpoint** - `/api/kb/search?q=<query>&limit=N` returns top-N matching entries with relevance score + snippet. Backed by simple TF-IDF (no external ML lib). Verified: endpoint returns ranked results for 10 test queries; top-3 are relevant to query.

10. **Weekly Digest Generator** - `python memory/archivist/weekly_digest.py` produces a summary: new entries added, entries updated, orphan changes, retrieval quality delta vs last week. Writes to memory/archivist/digest-WW-YYYY.md. Verified: script runs; digest file exists with all 4 sections populated.
