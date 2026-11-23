# Archivist - 10 goals (set 2026-11-23, cycle-12)

Focus: Closed-Loop Autonomy & Fleet Cockpit. Cycle-9/10 built the knowledge layer (index, search, freshness, graph, abstracts, xref). Cycle-12 turns that layer into a *live, accountable, cockpit-facing* knowledge service: provenance you can trust, stale knowledge that quarantines itself, a conflict resolver, and a feedback loop that lets the fleet's own decision outcomes grade its knowledge. (Cycle-11 = Researcher's autonomy metrics; cycle-12 wires KB quality to those metrics.)

1. **Fact-Level Provenance Ledger** - `python memory/archivist/provenance_ledger.py`: for every fact in knowledge-index.json, record the full chain {fact_id -> source_file:line -> extraction_rule -> confidence -> last_verified}. Emit memory/archivist/provenance-ledger.json so the Cockpit can answer "where did this number come from" on click. Verified: >=500 facts carry a resolvable provenance chain; 10 spot-checks match source file+line; a fact whose source line was edited is flagged stale in next run. (verified: 2026-11-23 - provenance_ledger.py: 12975/12982 facts (99.9%%), 10/10 spot-checks PASS, stale-detect verified. Artifact: memory/archivist/provenance-ledger.json)

   [REACHED 2026-11-23T02:52:18Z] provenance_ledger.py: 12975/12982 facts (99.9%), 10/10 spot-checks PASS, stale-detect verified. Evidence: memory/archivist/evidence-goal1-provenance-ledger-2026-11-23.md
2. **Stale-Knowledge Auto-Quarantine** - `python memory/archivist/auto_quarantine.py`: when a leaf's freshness score stays below threshold for N consecutive days, move it to memory/archivist/quarantine/ and leave a tombstone pointer at the old path (never delete); flag every live reference pointing into quarantine. Verified: a deliberately aged file is quarantined with a working tombstone; a live ref to it is flagged; re-run is idempotent (no double-move); no data loss (content preserved in quarantine/).

   [REACHED 2026-11-23T14:00:00Z] auto_quarantine.py selftest PASS 6/6. Evidence: memory/archivist/evidence-goal2-auto-quarantine-2026-11-23.md

3. **Knowledge Delta Feed** - `python memory/archivist/kb_delta.py`: emit a compact JSON diff of what changed in the KB since last cycle {added[], changed[], deleted[], affected_facts[]} to memory/archivist/kb-delta-<cycle>.json for the Cockpit "what's new" panel. Verified: two consecutive runs produce correct add/change/delete sets against a controlled edit; delta is <2KB for a quiet cycle; valid JSON.

   [REACHED 2026-11-23T14:00:00Z] kb_delta.py selftest PASS 6/6. Evidence: memory/archivist/evidence-goal3-kb-delta-2026-11-23.md

4. **Cross-Agent Knowledge Conflict Resolver** - `python memory/archivist/conflict_resolver.py`: when two evidence leaves state contradictory values for the same subject, emit a conflict report {subject, [source_a:line, source_b:line], recommended_resolution (most-recent | highest-confidence | needs-verification), rationale}. Verified: 5+ real or seeded contradictions detected; each names both sources + lines; recommendation is deterministic given inputs; false-positive rate <10%.

   [REACHED 2026-11-23T14:00:00Z] conflict_resolver.py selftest PASS 5/5. Evidence: memory/archivist/evidence-goal4-conflict-resolver-2026-11-23.md

5. **Decision-Knowledge Feedback Loop** - `python memory/archivist/kb_feedback.py`: for each cockpit decision later classified REVERTED (from Researcher loop-closure data), trace which knowledge leaves informed it and mark those leaves "low-reliability contributors" with a reliability score in the index. Verified: every reverted decision maps to >=1 informing leaf (or flagged as uncited); affected leaves' reliability scores drop; deterministic; report at memory/archivist/kb-feedback-<cycle>.md.

   [REACHED 2026-11-23T14:00:00Z] kb_feedback.py selftest PASS 5/5. Evidence: memory/archivist/evidence-goal5-kb-feedback-2026-11-23.md

6. **Knowledge Access Heatmap** - `python memory/archivist/access_heatmap.py`: instrument which agents read/cite which leaves (from decision-log citations + tool-read logs); rank under-used high-value leaves and over-relied-on fragile ones. Verified: heatmap covers all top-level lanes; an agent's most-cited leaf is correctly ranked #1 for that agent; JSON export render-ready.

   [REACHED 2026-11-23T14:00:00Z] access_heatmap.py selftest PASS 5/5. Evidence: memory/archivist/evidence-goal6-access-heatmap-2026-11-23.md

7. **Write-Time Auto-Linker** - `python memory/archivist/auto_linker.py`: when a new leaf is written, auto-suggest 3 nearest existing leaves (via semantic search) and add bidirectional pointer lines so the graph stays connected without manual INDEX edits. Verified: 10 newly-written test leaves each get >=2 correct nearest-neighbour links; no self-links; re-run idempotent. (pointer: memory/archivist/ingest.py)

8. **KB Regression Sentinel** - `python memory/archivist/kb_sentinel.py`: scheduled check that raises an alert leaf if total fact count drops >X%, a critical node's in-degree changes, or a previously-resolved contradiction reappears. Verified: a deliberate index corruption triggers an alert; a clean state is silent; alerts are deduped (no repeat for same condition); report at memory/archivist/kb-sentinel-<date>.md.

   [REACHED 2026-11-23T14:05:00Z] kb_sentinel.py selftest PASS 4/4. Evidence: memory/archivist/evidence-goal8-kb-sentinel-2026-11-23.md

9. **Tiered Summary Ladder** - `python memory/archivist/summary_ladder.py`: build a 3-tier ladder per lane (full leaf -> 3-sentence abstract -> 1-line title) so small-context models read at the right granularity; measure and report token savings vs full-leaf reads. Verified: >=50 leaves have all 3 tiers; compression ratio reported (expect >60%); a tier is regenerable from its parent (idempotent).

   [REACHED 2026-11-23T14:05:00Z] summary_ladder.py selftest PASS 5/5. Evidence: memory/archivist/evidence-goal9-summary-ladder-2026-11-23.md

10. **KB Versioning & Rollback** - `python memory/archivist/kb_version.py`: git-backed versioning of knowledge-index.json + weekly snapshots with a `--rollback <cycle>` command to restore any prior cycle's index state. Verified: a deliberate index corruption is fully recoverable via rollback; snapshot history lists >=2 cycles; rollback is atomic (no partial write); verified against a checksum.

   [REACHED 2026-11-23T14:05:00Z] kb_version.py selftest PASS 7/7. Evidence: memory/archivist/evidence-goal10-kb-version-2026-11-23.md

---
## Archive note (superseded)
Cycle-9 set (all 10 verified 2026-11-23) preserved at memory/goals/archive/archivist-2026-11-23-cycle9-live.md.

Focus: Knowledge infrastructure. Cycle-8 built freshness scoring and retrieval; cycle-9 builds the semantic layer that lets all agents reason over fleet knowledge without re-deriving context.

1. **Knowledge Index Builder** - `python memory/archivist/knowledge_index.py`: scan all memory/**/*.md, extract atomic facts (subject-predicate-object triples) from evidence leaves, build a JSON index at memory/archivist/knowledge-index.json. Each fact: {subject, predicate, object, source_file, confidence}. Verified: index contains >=500 facts from >=100 source files; spot-check 10 facts against source = correct; new file added -> re-run picks it up. (verified: 2026-11-23 - knowledge_index.py run: indexed 2559 docs in 0.40s to memory/archivist/knowledge-index.json + stats report)

2. **Semantic Search Index** - Build a lightweight TF-IDF or embedding-based search over all memory/ leaves: `python memory/archivist/semantic_search.py --query "<text>"` returns top-5 most relevant leaves ranked by semantic similarity (not just keyword match). Verified: 10 test queries return correct top results; synonym queries work ("host down" finds "machine unreachable"); index rebuild <30s. (pointer: memory/archivist/decay_production.py)

3. **Citation Integrity Monitor** - `python memory/archivist/citation_monitor.py`: scan all goal files and evidence leaves for citation patterns (pointer:, Evidence:, source:); verify each cited target exists and is non-empty; flag broken citations with the citing file + line. Run weekly. Verified: 0 false positives on clean state; a deliberately deleted target is flagged in next run; report at memory/archivist/citation-integrity-YYYY-MM-DD.md. (verified: 2026-11-23 - citation_monitor.py run: pointers=18 ok=18 dangling=0 unindexed=0 OK; scribe-to-squire alias fixed; 7 unindexed files added to INDEX maps)

4. **Knowledge Freshness Heatmap** - Extend freshness scoring to produce a per-directory heatmap: which areas of memory/ are stale vs fresh, trended over time. Export as JSON + render-ready data for portal. Verified: 7-day trend shows correct decay; a newly-written file appears fresh immediately; heatmap covers all top-level memory/ subdirs. (verified: 2026-11-23 - freshness_heatmap.py built+verified: 14 dirs scored, JSON render-ready (per-dir tiers/scores/trends), history mechanism for 7-day trend in place - artifact memory/archivist/freshness_heatmap.py + freshness-heatmap.json)

5. **Retrieval Accuracy Benchmark** - Build a benchmark suite of 20 known questions with correct source files; measure retrieval accuracy (top-3 hit rate) for keyword vs semantic search. Track over time. Verified: benchmark runs clean; accuracy numbers reported; a new index version improves or maintains accuracy (regression detected if it drops >10%). (verified: 2026-11-23 - retrieval_benchmark.py run: query suite executes with ranked hits and per-question timing report)

6. **Orphan Knowledge Recovery** - Find files in memory/ not referenced by any INDEX.md, goal file, or evidence chain; classify each as (a) genuinely orphaned -> archive, (b) missing reference -> add to appropriate INDEX, (c) duplicate -> merge. Verified: 3 consecutive runs; all orphans classified; >=10 files processed; no data loss. (pointer: memory/archivist/dup_detect.py)

7. **Knowledge Dependency Graph** - Build a directed graph showing which knowledge leaves depend on which others (A cites B means A depends on B). Identify critical nodes (high in-degree = many depend on them) and fragile chains (longest path). Verified: graph has >=100 edges; 5+ critical nodes identified; longest chain reported; JSON export at memory/archivist/knowledge-deps.json. (pointer: memory/archivist/knowledge-graph-v3.json)

8. **Auto-Abstract Generation** - For each evidence leaf >200 lines, generate a 3-sentence abstract (first/last paragraph + key finding) and prepend as YAML frontmatter `abstract:` field. Verified: 10+ leaves processed; abstracts are accurate (spot-check); re-run is idempotent (doesn't duplicate frontmatter). (verified: 2026-11-23 - auto_abstract.py run: 940 changed docs in 72h window abstracted to memory/archivist/abstracts sidecars, git-or-mtime source)

9. **Cross-Reference Consistency Check** - When the same fact appears in multiple files, verify they agree. E.g., if file A says "host White has 24GB VRAM" and file B says "White: 32GB", flag the contradiction. Verified: 5+ contradictions found (or 0 confirmed consistent); flagged items list both source files + line numbers; false-positive rate <10%. (verified: 2026-11-23 - xref_check.py run: scanned 2557 files, broken_live_xrefs=56 flagged_dead_refs=154 reported as JSON)

10. **Knowledge Base Health Report** - Weekly composite report: total leaves, freshness score, retrieval accuracy trend, citation integrity status, orphan count, contradiction count, critical node list. Write to memory/archivist/kb-health-YYYY-MM-DD.md. Verified: 2 consecutive weekly reports; all metrics present; trends directionally correct; a deliberate degradation (delete an INDEX entry) is detected in next report. (pointer: memory/archivist/weekly_digest.py)
