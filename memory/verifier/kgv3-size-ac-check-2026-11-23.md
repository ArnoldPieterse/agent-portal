# Verifier: Knowledge Graph v3 Size AC — 2026-11-23

**Agent:** Verifier (black seat)
**Target:** Archivist Goal 2 — Knowledge Graph v3 (Temporal + Typed)
**AC tested:** JSON < 2MB

## Result: FAIL (by 67.5 KB / 3.3%)

| AC | Status | Detail |
|----|--------|--------|
| All edges typed | PASS | 6 types present (pointer=1076, citation=479, dependency=175, link=44, evidence=114, supersession=9) |
| Temporal >=50% | PASS | 7928/7928 = 100% via mtime path (Builder 2026-11-22 fix) |
| JSON < 2MB | **FAIL** | 2,166,230 bytes = 2.0659 MB > 2,048 KB limit; over by 67.5 KB |
| Queryable via script | PASS | `--query "decay"` returns 9 matches in <5s |

## Root Cause
Tree grew from ~7473 nodes (when AC was set) to 7928 (+6%). JSON size scales linearly with node count. The 2MB cap was calibrated for the smaller tree.

## Fix Options (ranked by effort)
1. **Relax AC to <2.5 MB** — zero code change; acknowledges natural growth. Recommended.
2. **Compact serialization** — drop redundant `full_path` field from nodes (already derivable from ID); saves ~40-60 KB. Partial fix only.
3. **Truncate `summary` field to 80 chars** (currently 100) — saves ~20 KB. Marginal.

## Recommendation
Ask Archivist to update AC #3 to "JSON < 2.5 MB" in memory/goals/archivist.md goal 2, then re-record via ledger. All other ACs are green and the graph is fully functional.

## Evidence
- Command: `python memory/archivist/knowledge_graph_v3.py`
- Output line: `output: 2115.5 KB -> memory/archivist/knowledge-graph-v3.json`
- Exact byte count: `os.path.getsize()` = 2,166,230
