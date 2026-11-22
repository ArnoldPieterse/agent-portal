# Archivist - 10 goals (set 2026-11-23, cycle-9)

Focus: Knowledge infrastructure. Cycle-8 built freshness scoring and retrieval; cycle-9 builds the semantic layer that lets all agents reason over fleet knowledge without re-deriving context.

1. **Knowledge Index Builder** - `python memory/archivist/knowledge_index.py`: scan all memory/**/*.md, extract atomic facts (subject-predicate-object triples) from evidence leaves, build a JSON index at memory/archivist/knowledge-index.json. Each fact: {subject, predicate, object, source_file, confidence}. Verified: index contains >=500 facts from >=100 source files; spot-check 10 facts against source = correct; new file added -> re-run picks it up.

2. **Semantic Search Index** - Build a lightweight TF-IDF or embedding-based search over all memory/ leaves: `python memory/archivist/semantic_search.py --query "<text>"` returns top-5 most relevant leaves ranked by semantic similarity (not just keyword match). Verified: 10 test queries return correct top results; synonym queries work ("host down" finds "machine unreachable"); index rebuild <30s. (pointer: memory/archivist/decay_production.py)

3. **Citation Integrity Monitor** - `python memory/archivist/citation_monitor.py`: scan all goal files and evidence leaves for citation patterns (pointer:, Evidence:, source:); verify each cited target exists and is non-empty; flag broken citations with the citing file + line. Run weekly. Verified: 0 false positives on clean state; a deliberately deleted target is flagged in next run; report at memory/archivist/citation-integrity-YYYY-MM-DD.md.

4. **Knowledge Freshness Heatmap** - Extend freshness scoring to produce a per-directory heatmap: which areas of memory/ are stale vs fresh, trended over time. Export as JSON + render-ready data for portal. Verified: 7-day trend shows correct decay; a newly-written file appears fresh immediately; heatmap covers all top-level memory/ subdirs.

5. **Retrieval Accuracy Benchmark** - Build a benchmark suite of 20 known questions with correct source files; measure retrieval accuracy (top-3 hit rate) for keyword vs semantic search. Track over time. Verified: benchmark runs clean; accuracy numbers reported; a new index version improves or maintains accuracy (regression detected if it drops >10%).

6. **Orphan Knowledge Recovery** - Find files in memory/ not referenced by any INDEX.md, goal file, or evidence chain; classify each as (a) genuinely orphaned -> archive, (b) missing reference -> add to appropriate INDEX, (c) duplicate -> merge. Verified: 3 consecutive runs; all orphans classified; >=10 files processed; no data loss. (pointer: memory/archivist/dup_detect.py)

7. **Knowledge Dependency Graph** - Build a directed graph showing which knowledge leaves depend on which others (A cites B means A depends on B). Identify critical nodes (high in-degree = many depend on them) and fragile chains (longest path). Verified: graph has >=100 edges; 5+ critical nodes identified; longest chain reported; JSON export at memory/archivist/knowledge-deps.json. (pointer: memory/archivist/knowledge-graph-v3.json)

8. **Auto-Abstract Generation** - For each evidence leaf >200 lines, generate a 3-sentence abstract (first/last paragraph + key finding) and prepend as YAML frontmatter `abstract:` field. Verified: 10+ leaves processed; abstracts are accurate (spot-check); re-run is idempotent (doesn't duplicate frontmatter).

9. **Cross-Reference Consistency Check** - When the same fact appears in multiple files, verify they agree. E.g., if file A says "host White has 24GB VRAM" and file B says "White: 32GB", flag the contradiction. Verified: 5+ contradictions found (or 0 confirmed consistent); flagged items list both source files + line numbers; false-positive rate <10%.

10. **Knowledge Base Health Report** - Weekly composite report: total leaves, freshness score, retrieval accuracy trend, citation integrity status, orphan count, contradiction count, critical node list. Write to memory/archivist/kb-health-YYYY-MM-DD.md. Verified: 2 consecutive weekly reports; all metrics present; trends directionally correct; a deliberate degradation (delete an INDEX entry) is detected in next report. (pointer: memory/archivist/weekly_digest.py)
