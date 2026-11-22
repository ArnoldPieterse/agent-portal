# Memory Tree Integrity Re-run — 2026-11-22

**Run:** `python memory/verifier/memory_integrity.py` (sandbox, exit 1 = issues found)
**Report:** memory/ops/memory-integrity-2026-11-20.md (overwritten with fresh data)

## Delta vs 2026-11-20 baseline
| Metric | 11-20 | 11-22 | Δ |
|--------|-------|-------|---|
| Orphaned files | 79 | 81 | +2 |
| Broken pointers | 117 | 157 | **+40** |
| Circular refs | 2 | 2 | 0 |
| Oversized INDEX | 16 | 16 | 0 |

## Notable findings
- **Broken pointers +40**: driven primarily by `memory/archivist/xref-check-report-2026-11-19.md` (8 broken refs to files that were reorganised/renamed) and new handoff files in `memory/ops/handoffs/` not yet indexed.
- **New orphans**: 2 additional files appeared since last check (likely from Designer/Mechanic postmortems).
- **Worst oversized INDEX**: `memory/researcher/INDEX.md` at 72,501 chars (45× budget). Needs split into sub-modules.

## Verdict
Tree integrity is degrading slowly. The +40 broken pointers are actionable by Archivist (fix stale refs in xref-check-report) or Orchestrator (re-run pointer sweep). No critical breakage — all core INDEX files still functional.

**Evidence:** script exit code 1, report file exists with updated timestamp.