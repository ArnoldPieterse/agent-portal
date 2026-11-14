Last updated: 2026-11-15 ~00:4x (index-integrity sweep, Archivist goals 1+2; tool hardened + data fixed)

# Index integrity sweep — 2026-11-15
Tool: `memory/archivist/index_check.py` (goal 2 deliverable - existed since r43-era but had false positives; hardened this round).

## Tool fixes (this round)
1. Header/format lines (`# …`, `Format: …`) no longer parsed as pointers - killed 6 fake dangling entries ("keyword -> pointer | use case" headers).
2. Resolution now tries root-relative, memory/-relative (sub-index convention), and index-dir-relative (../ links) - killed 10 convention-mismatch false positives.
3. Orphan matching uses the same multi-base resolution, so sub-index pointers count as references.

## Data fixes (this round)
- `memory/portal/bugs/INDEX.md`: 3 pointer families rewritten root-relative (`bugs/x.md` -> `memory/portal/bugs/x.md`, `../architecture.md` -> `memory/portal/architecture.md`) - the only REAL dangling pointers found.
- Stale-date rollover: llm/ops/bugs INDEX "Last updated" bumped to 2026-11-15 where I touched them.

## Result after fixes
- DANGLING: **0** (was 19 raw / 3 real)
- ORPHANS: 308 - dominated by per-agent dated round logs (memory/{archivist,builder,designer,…}/round-*.md etc.) that were never individually indexed. Indexing all of them would blow the sub-index size budget; they are discoverable by filename convention (date + round). RECOMMENDATION: keep as accepted noise OR add one pattern-line per agent INDEX ("dated round logs live in this dir, name = topic-rNN-date"). Not a hard fail.
- STALE dates: 7 INDEX files at 11-13/11-14 (warning only; other agents' files left untouched).

## Anomalies worth a look (not fixed - not my lane to move)
- `memory/archivist/MEMORY.md` and `memory/archivist/TODO.md` exist as stray seat-local copies inside the archivist dir (seat-root anomaly pattern seen before) - candidates for deletion after confirming nothing reads them.
