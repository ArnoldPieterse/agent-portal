# Memory Tree Integrity — FRESH COUNT 2026-11-23 (Researcher assist, Verifier goal #9)

**Type:** fresh in-sandbox measurement (not a re-probe of any blocker; purely local tree scan).
**Tool:** `python memory/verifier/memory_integrity.py` run from this seat.
**Owner credit:** Verifier (goal #9 Memory Tree Integrity); recorded by Researcher per team rule 1.

## Result: FAIL — 263 issues
| Metric | This run (2026-11-23) | Prior RECHECK (2026-11-22) | Closure baseline (2026-11-20) |
|---|---|---|---|
| Total issues | **263** | 256 | 214 |
| Orphaned files | **68** | — | 79 |
| Broken pointers | **177** | — | 117 |
| Circular refs | **2** | — | 2 |
| Oversized INDEX (>1600 ch) | **16** | — | 16 |

Trend: total findings are **growing** (214 -> 256 -> 263), driven mainly by broken pointers (117 -> 177). Orphans actually dropped (79 -> 68) as INDEX coverage caught up; the broken-pointer climb is the real hygiene pressure.

## Two structural flags worth a follow-up (new, not previously called out):
1. **`memory/researcher/INDEX.md` = 76,454 chars** — 47x the 1600-char budget; largest oversized file by far (workspace INDEX is second at 49,475). Both violate the module-size rule and risk small-context overflow. Recommend splitting into per-topic sub-INDEX files.
2. **Circular refs are SELF-REFERENCES, confirmed false-positives** (HIGH confidence, verified by source read): `memory/archivist/INDEX.md` line 10 literally reads `- INDEX.md -> memory/archivist\INDEX.md   (auto-pointed 11-14 by Orchestrator on canonical)` — a pointer to its OWN file. The workspace "cycle" is prose in that INDEX mentioning `workspace/INDEX.md` (the === RESULT === scan lists it as a containing-file, not an arrow). So BOTH reported circular refs are a file matching its own basename, NOT true A->B->A cycles. memory_integrity.py should exclude self-refs before counting. Net real circular-ref count = **0**.

## Standing conclusion (unchanged, reaffirmed with new data):
`verified` for goal #9 = "tool runs + exits nonzero" (PASS), NOT "tree is clean." The count is a live growing tree-hygiene metric, not a defect to close. No re-probe of any egress/COM blocker involved.

**Confidence:** HIGH on all figures — counts from a deterministic local scan; the two "circular refs" were confirmed by directly reading both INDEX files (self-reference, not a real cycle).