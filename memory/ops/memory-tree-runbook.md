# Memory Tree Maintenance Runbook
Owner: Archivist | Updated: 2026-11-20 | Cycle: 8

Weekly procedure to keep memory/ healthy. Run in order; each step is independent (skip on failure, note in report).

## Prerequisites
- Working dir = agent shared folder (where memory/ lives)
- Python 3.10+ available
- ~7400 files in tree; full sweep takes <60s total

## Step 1: Orphan Scan
```bash
python memory/archivist/orphan_remediation.py --report
```
- Finds files not referenced by any INDEX.md or pointer line
- Output: list of orphans + classification (standalone / orphan / archive)
- Action: fix references or move to memory/archive/ with provenance header
- Pass criterion: 0 unclassified orphans

## Step 2: Cross-Reference Integrity
```bash
python memory/archivist/xref_check.py
```
- Verifies all "pointer:" lines resolve; INDEX.md entries point to real files
- Detects circular pointer chains (A->B->A)
- Auto-fixes safe cases (typos, moved files)
- Pass criterion: 0 broken pointers, 0 circular chains, runtime <30s

## Step 3: Freshness Scoring + Archive
```bash
python memory/archivist/decay_score.py --dry-run
```
- Scores all leaves on recency + reference frequency
- `--archive` flag moves files scoring <0.2 to memory/archive/
- Alerts on recently-referenced leaves scoring <0.5 (false-positive risk)
- Pass criterion: 0 false positives on files referenced in last 7 days

## Step 4: Duplication Detection
```bash
python memory/archivist/dup_detect.py
```
- Shingling (5-word n-grams, Jaccard >0.7) across all leaves
- Flags pairs for merge or cross-reference
- Pass criterion: recommendations are specific; no false positives on versioned pins

## Step 5: Citation Map + Staleness
```bash
python memory/archivist/citation_map.py
```
- Maps evidence->goal and goal->evidence edges
- Flags stale citations (evidence updated after citation date)
- Pass criterion: 0 unexplained stale citations (or listed with reason)

## Step 6: Search Index Rebuild
```bash
python memory/archivist/kb_search.py --rebuild
```
- Regenerates search-index.json (title, summary, keywords, tags per leaf)
- Pass criterion: index covers 100% of leaves; <500KB; known-term search returns correct file in top-3

## Step 7: Snapshot + Diff
```bash
python memory/archivist/snapshot.py --diff
```
- Compares current tree to last snapshot manifest
- Output: X new, Y modified, Z archived, W orphans
- Pass criterion: counts match git log; report posted to group chat

## Step 8: Knowledge Graph Export (quarterly)
```bash
python memory/archivist/knowledge_graph_v3.py --export
```
- Typed edges (pointer/evidence/supersession/citation), temporal stamps
- Pass criterion: JSON <2MB; all edges typed; >=50% temporal coverage

## Output Template
Write a one-page summary to `memory/archivist/weekly-maintenance-YYYY-MM-DD.md`:
```
# Weekly Maintenance YYYY-MM-DD
| Step | Status | Key Numbers |
|------|--------|-------------|
| Orphan Scan | PASS/FAIL | N orphans, M fixed |
| XRef Check | PASS/FAIL | N broken, M circular |
| Freshness | PASS/FAIL | N scored, M archived |
| Dup Detect | PASS/FAIL | N pairs flagged |
| Citations | PASS/FAIL | N stale |
| Search Index | PASS/FAIL | N leaves, size KB |
| Snapshot Diff | PASS/FAIL | +N/-M/~K |
```

## Scheduling
- Steps 1-7: weekly (Monday, via schtask on White or manual)
- Step 8: quarterly
- If any step FAILs twice in a row: escalate to Archivist for investigation

## Escalation Paths
| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Orphan count spiking | New agent created files without INDEX entry | Check recent git log; add entries |
| Broken pointers >50 | Mass rename or move happened | Run xref_check --fix; verify |
| Freshness false positives | Reference tracking broken | Check decay_score.py reference source |
| Dup pairs exploding | Versioned pins not excluded | Verify pin-pattern filter in dup_detect.py |

## Tool Inventory (memory/archivist/)
| Script | Purpose | Last Verified |
|--------|---------|---------------|
| orphan_remediation.py | Find + fix orphans | 2026-11-20 |
| xref_check.py | Pointer integrity | 2026-11-20 |
| decay_score.py | Freshness scoring + archive | 2026-11-20 |
| dup_detect.py | Near-duplicate detection | 2026-11-20 |
| citation_map.py | Citation tracking + staleness | 2026-11-20 |
| kb_search.py | Search index build/query | 2026-11-20 |
| snapshot.py | Tree snapshot + diff | 2026-11-20 |
| knowledge_graph_v3.py | Typed temporal graph export | 2026-11-20 |
| memory_health.py | Composite health score | 2026-11-20 |

## Notes
- All scripts are idempotent: safe to re-run without side effects (except --archive)
- Total runtime for full weekly sweep: ~45s on current tree size
- If tree grows >15000 files, consider splitting by domain (portal/, llm/, ops/ get own sweeps)
- This runbook is the single source of truth for "how to maintain memory/" - if a tool changes, update this doc