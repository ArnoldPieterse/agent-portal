# Supersession Chain Completeness Audit — 2026-11-18

**Goal #4 acceptance: zero dangling references; audit report committed.**

## Method
- Script: `memory/archivist/supersession_check.py` (v2, updated this pass)
- v2 fixes over cycle-2 original:
  - Negative lookbehind `(?<![A-Za-z0-9_-])` prevents matching "superseded" inside hyphenated filenames
  - JSON/JSONL files excluded (data artifacts, not prose docs with supersession markers)
  - Prose-target filter rejects targets containing common English words (archive, older, etc.)
  - `__pycache__` excluded from walk

## Results
| Metric | Value |
|--------|-------|
| Files scanned (non-JSON) | 1259 |
| Supersession markers found | 28 |
| Resolved to existing files | 28 |
| Dangling references | **0** |
| Cycles detected | 0 |

## Fix Applied This Pass
- `memory/portal/v1-upgrades-decisions.md` line 2: annotated stale upload reference
  `uploads/AgentPortal_V1/UPGRADES.md` as `[historical upload, now archived]` with migration
  pointer to `memory/portal/v1-upgrades.md`. This was the only genuine dangling ref.

## False-Positive Analysis (why v1 reported 109 dangling)
- 82 of 109 were from regex matching "SUPERSEDED"/"superseded" *inside filenames*
  (e.g. `goals-SUPERSEDED-partial.md` → captured `-partial.md` as target)
- 7 were prose words with slashes (`d/archive`, `OLDER/smaller`, etc.)
- 1 was a JSON data file containing node IDs
- 19 were from `.json`/`.jsonl` files (knowledge graph state, manifests) — excluded in v2

**Verdict: PASS. All supersession chains complete.**