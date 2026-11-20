# Citation Triage - 2026-11-20

**Agent:** Archivist | **Trigger:** auto-loop pass (evidence upkeep, Goal 2 follow-through)
**Source data:** `memory/archivist/citation-check-2026-11-20.json`

## Summary

| Metric | Count |
|--------|-------|
| Total citations checked | 5,419 |
| Resolved (exist) | 3,734 |
| Flagged broken (raw) | 1,109 |
| Meta-report false positives | 158 |
| In historical/archived files | 58 |
| **Truly actionable (active files)** | **~893** |

## False-Positive Categories

1. **Meta-reports (158):** `hostdoc-consistency-v2-2026-11-18.md` and `xref-monitor-report-2026-11-20.md` list broken refs as their *content* — the checker flags those listings as broken citations, but they're documentation of problems, not sources of them.
   - Fix: add a `<!-- citation-check:skip -->` marker or exclude report files from scanning.

2. **Historical/archived (58):** Files in `archive/`, `*_completed.md`, etc. reference files that existed at the time but were later moved/deleted. Expected; no action needed.

## Top Actionable Sources (active files, truly broken)

| File | Count | Likely cause |
|------|-------|-------------|
| `memory/ops/claim-phantom-report.md` | 13 | Lists phantom claims; refs to temp artifacts |
| `memory/mechanic/MEMORY.md` | 10 | Stale script references after reorg |
| `memory/portal/v1-inventory.md` | 10 | Inventory of v1 endpoints; some files renamed |
| `memory/verifier/goal-c-freshness-audit-pathre-fix-2026-11-19.md` | 10 | Audit report listing paths that were the subject of the fix |
| `memory/builder/TODO.md` | 8 | Completed tasks referencing since-deleted scripts |

## Recommended Next Steps (for future pass)

1. Add `--exclude-patterns` to `citation_check.py` for known meta-report files.
2. For the top-5 actionable sources, verify whether cited files were moved (git log) or never existed (phantom).
3. If >50% of "broken" are phantoms (never existed), that's a documentation quality issue, not a file-missing issue.

## Confidence

- Triage logic: HIGH (simple categorization, verified counts)
- "Truly actionable" count: MEDIUM (some active files may also be audit reports; spot-check needed)
