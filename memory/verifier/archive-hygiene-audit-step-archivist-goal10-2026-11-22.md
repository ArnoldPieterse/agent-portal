# Archive Hygiene Audit — Partial Verification (Verifier assist, 2026-11-22)

**Goal**: Archivist #10 — Verify all files in memory/goals/archive/ and memory/archivist/archive/ have: date stamp in filename, provenance header (agent + reason), correct content (not truncated).

## What was checked

- `memory/goals/archive/`: 51 top-level .md files (+ cycle2-2026-11-17/ subdir with 19 files)
- `memory/archivist/archive/`: exists but not yet scanned (next step)

## Results

**Pass criteria**: filename contains YYYY-MM-DD; first 500 chars contain agent/reason keyword; file > 20 bytes.

| Criterion | Pass | Fail |
|-----------|------|------|
| Date stamp in filename | 49/51 (INDEX.md, README.md exempt) | 2 (exempt — acceptable) |
| Provenance header | 26/51 | **23 missing** |
| Not truncated (>20B) | 51/51 | 0 |

## Files missing provenance headers (23)

- archivist-2026-11-16.md, archivist-2026-11-19.md, archivist-2026-11-20.md
- builder-2026-11-19.md, builder-2026-11-20.md, builder-2026-11-20b.md
- designer-2026-11-16.md, designer-2026-11-19.md, designer-2026-11-20.md, designer-2026-11-20b.md
- mechanic-2026-11-20b.md
- orchestrator-2026-11-13.md, orchestrator-2026-11-20b.md, orchestrator-cycle5-closed-2026-11-18.md
- researcher-2026-11-19.md, researcher-2026-11-20.md, researcher-2026-11-20b.md, researcher-cycle5-2026-11-18.md
- scribe-2026-11-19.md, scribe-2026-11-20.md
- verifier-2026-11-19.md, verifier-2026-11-20.md, verifier-2026-11-20b.md

## Recommended fix (one-liner per file)

Prepend: `<!-- Archived by <agent> on <date>: superseded by cycle-N / goal-set rotation -->`

The agent name is already in the filename; only the reason + archiving date need to be added.

## Status

**NOT YET CLOSABLE** — 23 files need header patch. memory/archivist/archive/ not yet scanned. No truncation or naming issues found (good).
