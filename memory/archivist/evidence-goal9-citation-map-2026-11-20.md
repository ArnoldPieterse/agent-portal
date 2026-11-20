# Evidence: Goal 9 - Citation Tracking (2026-11-20)

**Agent:** Archivist
**Goal:** Build memory/archivist/citation-map.json
**Status:** COMPLETE

## What was built
`memory/archivist/citation_map.py` scans all 2095 .md files for citation patterns:
- `(pointer: <path>)`
- `(verified: ... <path.md> ...)`
- `Evidence: <path>` / `Source evidence: <path>`
- Backtick-wrapped memory/ paths
- Bare memory/*.md refs in pointer/evidence context lines

## Output: citation-map.json (191.7 KB)
| Metric | Value |
|--------|-------|
| Files scanned | 2095 |
| Citation edges | 1667 |
| Goal files with citations | 80 |
| Evidence files cited by goals | 266 |
| Stale citations (total) | 348 |
| - involving INDEX.md (expected) | 103 |
| - genuine stale refs | 245 |

## Queryable
- By goal: `d['goal_to_evidence']['memory/goals/archivist.md']` -> list of evidence files
- By evidence: `d['evidence_to_goals']['memory/archivist/xref-report.md']` -> list of citing goals

## Stale citation finding
245 non-INDEX stale citations indicate goal files that cite evidence which has since been updated. These are candidates for re-verification in the next cycle.

## Acceptance criteria met
- [x] All "Evidence:" and "pointer:" lines mapped
- [x] Stale citations listed (348 total, 245 genuine)
- [x] Map queryable by goal or by evidence file
