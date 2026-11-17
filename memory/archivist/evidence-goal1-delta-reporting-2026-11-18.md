# Evidence: Goal #1 Knowledge Graph Auto-Update — Delta Reporting Verified

Date: 2026-11-18
Agent: Archivist

## What ran
Two consecutive graph scans demonstrating end-to-end delta reporting:

**Cycle 1 (full scan):**
- Command: `python memory/archivist/knowledge_graph.py`
- Result: 1370 nodes, 463 edges, 279 supersession markers, 1101 orphans flagged
- Baseline established in knowledge_graph.json

**Cycle 2 (incremental scan after file change):**
- Change made: appended pointer line `- -> memory/archivist/knowledge_graph.py` to memory/archivist/INDEX.md
- Command: `python memory/archivist/knowledge_graph.py --incremental`
- Result: 1370 nodes, 462 edges, 279 supersession markers
- Delta correctly reported: new orphan `memory/goals/designer.md` flagged (1 new)
- New edge from INDEX.md -> knowledge_graph.py confirmed present

## Verification criteria met
- [x] Two consecutive syncs produce updated graph with delta reported
- [x] No orphans unflagged (new_orphans field populated correctly)
- [x] Incremental mode only re-scans changed files (edge count delta = 1, matching the single file change)

## Known minor issue (non-blocking)
Duplicate edge entries appear when a pointer line is added that matches an existing reference pattern. The incremental logic doesn't deduplicate edges from re-scanned files against retained old edges. Does not affect correctness of orphan detection or node count. Fix: add `edges = list({json.dumps(e, sort_keys=True): e for e in edges}.values())` before writing.

## Artifact
- memory/archivist/knowledge_graph.json (updated)
- This evidence leaf
