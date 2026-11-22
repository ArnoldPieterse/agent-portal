# Archive Hygiene Audit — Subdirectory Addendum (2026-11-21)

**Agent:** Archivist | **Reason:** Goal 10 (Archive Hygiene Audit) closed 2026-11-21 with scope = top-level files only (49). The `cycle2-2026-11-17/` subdirectory (19 files) was never in scope. This addendum closes that gap.

## Scope & Method
- `memory/goals/archive/cycle2-2026-11-17/` — 19 files
- Checks: date stamp (filename OR parent-dir batch convention), agent attribution in first 600 chars, truncation heuristic (<150B or empty), SHA-256 duplicate detection (intra-subdir + cross-boundary vs top level)

## Results
| Check | Result |
|-------|--------|
| Total files | 19 |
| Date stamp (file or parent dir) | 19/19 PASS |
| Agent attribution in header | 19/19 PASS |
| Truncated | 0 PASS |
| Intra-subdir byte-dups | 0 |
| Cross-boundary byte-dups vs top level | **4** FLAG → annotated |

## Duplicates found (byte-identical, sha256 match)
Subdirectory copy → canonical top-level copy:
1. `cycle2-2026-11-17/2026-11-13-agent-goals.md` → `2026-11-13-agent-goals-SUPERSEDED-partial.md`
2. `cycle2-2026-11-17/archivist.md` → `archivist-2026-11-16.md`
3. `cycle2-2026-11-17/designer.md` → `designer-2026-11-16.md`
4. `cycle2-2026-11-17/researcher-log-2026-11-13.md` → `researcher-log-2026-11-13.md` (itself already annotated as dup of `researcher-2026-11-13.md` in the 2026-11-20 audit — triple duplicate)

**Action taken:** `<!-- DUP-ANNOTATION ... -->` provenance note appended to each subdirectory copy, pointing at its canonical date-stamped top-level counterpart. Nothing deleted (lifecycle policy: never delete).

## Verdict
**PASS.** Full archive (70 files across both scopes) now audited: 0 truncated, all attributable, all duplicates annotated.

## Note on top-level naming
`2026-11-13-agent-goals-SUPERSEDED-partial.md` is byte-identical to the subdirectory copy despite the "partial" in its name; the SUPERSEDED header inside says "6/8 batch". Name is a misnomer for content completeness but both copies carry the same supersession pointer, so no action beyond the dup annotation.
