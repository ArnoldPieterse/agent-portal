# Archivist - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes the KB a production service: fast, reliable, self-maintaining, and queryable under load.

1. **KB Query Performance Benchmark** - `python memory/archivist/kb_benchmark.py`: measure KB search latency (p50, p95, p99) across 100 test queries of varying complexity; establish baseline; alert if p95 degrades >30% vs baseline. Emit memory/archivist/kb-bench-<date>.json. Verified: 100 queries executed; latency percentiles computed; a query that times out (>5s) is logged with the search term.

2. **KB Auto-Index Health Check** - `python memory/archivist/index_health.py`: on each pass, verify: (a) index file parses, (b) all indexed paths exist on disk, (c) no orphan files exist that should be indexed, (d) index count matches actual file count within 5%. Emit PASS/FAIL + details. Verified: >=4 checks run; a deliberately deleted indexed file is detected; an unindexed new file is flagged as orphan.

3. **Knowledge Graph Edge Validation** - `python memory/archivist/graph_validate.py`: validate the knowledge graph (from KB index cross-references): no dangling edges (pointing to non-existent nodes), no self-loops, no duplicate edges, connectivity check (no isolated clusters >1 node). Emit validation report. Verified: >=4 checks defined; a deliberately broken edge is detected; report lists all violations with source/target node IDs.

4. **KB Caching Layer** - `python memory/archivist/kb_cache.py`: implement an LRU cache for KB search results: key = (query_hash, index_version); invalidate on index change; measure hit rate and latency reduction vs uncached. Emit cache stats to memory/archivist/cache-stats-<date>.json. Verified: after 50 repeated queries, hit rate >60%; cached response is <10ms vs >100ms uncached; invalidation works after index update.

5. **KB Export & Import** - `python memory/archivist/kb_export.py`: export the full KB to a single portable JSON file (facts + graph + provenance); provide --import to restore from that file. Verified: export produces valid JSON <50MB; import into a fresh directory reproduces identical index; round-trip preserves all fields byte-identically.

6. **Stale Knowledge Auto-Refresh** - `python memory/archivist/auto_refresh.py`: for facts flagged as approaching staleness (from Researcher decay predictor), auto-trigger re-verification: re-read source, check if value changed, update KB entry or flag for manual review. Emit refresh report. Verified: >=5 facts refreshed; a fact whose source changed is updated with new value + timestamp; unchanged facts are marked "still valid" without modification.

7. **KB Access Pattern Analyzer** - `python memory/archivist/access_analyzer.py`: from portal logs + agent tool-read history, compute which KB leaves are most/least accessed per week; identify "hot" leaves (candidate for caching) and "cold" high-value leaves (candidate for promotion in index). Emit memory/archivist/access-<week>.md. Verified: >=20 leaves have access counts; top 5 "hot" leaves identified; at least 1 "cold but high-value" leaf is flagged with reasoning.

8. **KB Versioning & Diff** - `python memory/archivist/kb_version.py`: maintain a version history of the KB index (hash + timestamp per change); provide --diff <v1> <v2> to show what changed between versions; --rollback <version> to restore. Verified: >=3 versions captured; diff shows exact facts added/removed/changed; rollback restores byte-identical index.

9. **KB Search Relevance Feedback** - `python memory/archivist/relevance_feedback.py`: when an agent cites a KB leaf in a decision, log the (query -> cited_leaf) pair; periodically compute relevance score per query type; flag queries where top-3 results were never cited (poor ranking). Emit tuning report. Verified: >=20 query-citation pairs logged; 1 poorly-ranked query is identified with suggested index weight adjustment; adjustment improves that query's ranking on re-test.

10. **KB API Endpoint** - Add `/api/kb/search?q=<query>&limit=<n>` endpoint to portal: returns top-N matching KB leaves with {path, title, snippet, relevance_score}. Backed by the existing KB index. Verified: endpoint responds in <200ms for simple queries; returns >=3 results for common terms; 404 for empty query; results are ranked by relevance (not alphabetical).
