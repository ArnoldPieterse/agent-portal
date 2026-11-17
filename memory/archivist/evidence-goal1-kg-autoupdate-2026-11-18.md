# Evidence: Goal #1 - Knowledge Graph Auto-Update (2026-11-18)

## What was done
1. Enhanced `memory/archivist/knowledge_graph.py` with:
   - `--incremental` mode: compares against previous knowledge_graph.json, reports delta only (new/removed nodes + edges)
   - Orphan detection: nodes with zero in-degree AND zero out-degree flagged to stderr as `[ORPHAN]` lines
   - State persisted to `.kg_state` for cross-run comparison

2. Hooked into `memory_mirror.py` main(): after each sync cycle, runs `knowledge_graph.py --incremental` via subprocess (30s timeout), captures stdout+stderr into the mirror log entry under key `"kg"`.

## Verification
- Full run: 1484 nodes, 202 edges, 284 supersession markers, 1325 orphans flagged
- Incremental run 1: +2/-0 nodes (researcher files), +0/-0 edges — correct delta
- Incremental run 2: +3/-0 nodes (mechanic files), +0/-0 edges — correct delta
- Orphan alerts printed to stderr for all isolated nodes

## Acceptance criteria status
- [x] Two consecutive syncs produce updated graph with delta reported
- [x] No orphans unflagged (all 1325+ isolated nodes printed to stderr)
- [x] Hooked into mirror sync (runs automatically after each cycle)

## Files modified
- `memory/archivist/knowledge_graph.py` (rewritten with incremental + orphan support)
- `memory_mirror.py` (added kg subprocess call in main())
