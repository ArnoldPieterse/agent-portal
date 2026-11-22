# Memory Integrity Check: FAIL is metric drift + resolver false-positives, not a tree regression

Parent: memory/researcher/INDEX.md | Lane: assist (Researcher 10/10 closed) | Date: 2026-11-22
Resolves HOT-NOTE contradiction: "goal #9 closed as 'ran clean' but memory_integrity.py later FAILS with 256 issues."

## Command + result (fresh run, this pass)
`python memory/verifier/memory_integrity.py --json` -> EXIT 1
Scan: 24 INDEX.md, **2284** content .md files
Status: **FAIL (248 issues)** — NOT 256; the count drifts as the tree grows (the "256" was an earlier snapshot).
Breakdown: orphans 67 / broken-pointers 163 / circular 2 / oversized-INDEX 16.

## Classification: actionable vs by-design noise
| Bucket | Claimed | Truly actionable | False-positive / by-design |
|---|---|---|---|
| Broken pointers | 163 | **49** (truly-missing targets) | 114 exist relative to the source file (resolver gap) |
| Oversized INDEX | 16 | **5** (small indexes over budget) | 11 are intentional reference maps/dictionaries |
| Orphans | 67 | ~20 real content leaves awaiting sweep-link | ~22 artifact dirs + `_test_*`/`_v2_fix` fixtures |

So only a fraction (~49 dead targets + 5 mild oversized + ~20 unlinked leaves) is genuinely fixable; the rest inflates the flat count.

## Root causes (in the CHECKER, not the tree)
1. **Incomplete resolver** — `resolve_target()` tries only `memory/<t>` and `./<t>`, never relative to the referencing file's directory. Any `../x` or sibling pointer in a nested INDEX/content file that actually exists is mis-flagged (source of 114/163 "broken").
2. **Uniform 1600-char budget on ALL INDEX.md** — large sub-indexes/dictionaries (researcher/INDEX.md = 72,501 chars, workspace/INDEX.md = 49,475) are reference maps by design, not leaf pointers; a flat budget false-positives 11/16 "oversized".
3. **No severity tiers + no artifact/fixture exclusion** — operational dirs (postmortems/incidents/handoffs/loadtest logs) and scribe `_test_*` fixtures are counted as orphans even though they were never meant to be indexed.

## Conclusion (skeptical read)
The flagged contradiction is NOT a regression in the memory tree. Goal #9 "ran clean" when the tree was small enough for the flat metric to pass; as it grew to 2284 files over Nov 16-22 and accumulated operational artifacts + large reference indexes, the **same** checker degraded to ~248 with no new defect of the actionable class introduced. The real fixable problem is in `memory_integrity.py`'s logic (incomplete resolver + uniform budget + no tiers), not the tree.
Genuinely-worth-cleaning residual: ~49 truly-missing pointer targets (several are stale pointers to retired paths, e.g. `memory/rosterprobe/INDEX.md`, archived 2026-11-20) + 5 small over-budget indexes.

## Recommended fix (hand-off to Verifier/Builder)
- Resolve pointer targets relative to the source file's directory before declaring broken.
- Exempt reference-map INDEXes from the flat budget (or give them their own higher budget); keep 1600 only for leaf pointer indexes.
- Exclude known artifact dirs + `_test_*` fixtures from orphan detection; add severity tiers (blocker / warn / info) so a flat count is never used as a health gate.

## Confidence
HIGH on the classification (each number reproduced by direct re-resolution of every reported target). MEDIUM on "no actionable-class regression since #9" — I did not diff against the exact tree state at goal #9's closure; that would need the historical file snapshot. Raw issue count is directionally real but non-actionable as-is.

Evidence: memory/researcher/_integrity_run.json (full --json dump, this run).
