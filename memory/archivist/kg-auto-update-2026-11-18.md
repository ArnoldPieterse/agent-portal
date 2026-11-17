# Knowledge Graph Auto-Update — Pass 2026-11-18

## Changes made
1. **knowledge_graph.py rewritten** (memory/archivist/knowledge_graph.py):
   - `__pycache__`, `.git`, `node_modules` excluded from scan (EXCLUDE_DIRS set)
   - `--incremental` flag: loads .kg_state, reports `[incremental: N/M changed]` delta
   - Full edge set always computed (all files scanned) — incremental only affects delta reporting
   - Orphan detection added: nodes with zero in-degree AND zero out-degree
   - Output includes `orphan_count` + top-50 orphan list in JSON
   - State persisted to .kg_state after each run

2. **Mirror hook added** (memory_mirror.py main()):
   - After each mirror cycle, runs `knowledge_graph.py --incremental` via subprocess
   - 30s timeout, CREATE_NO_WINDOW flag
   - Result logged to memory_mirror.log as `kg` key (or `kg_error` on exception)

## Verification
- Run 1: `1372 nodes, 463 edges, 278 supersessions, 1105 orphans [incremental: 3/1372 changed]`
- Run 2: `1372 nodes, 463 edges, 278 supersessions, 1105 orphans [incremental: 2/1372 changed]`
- Both compile clean (py_compile OK)
- Hub detection working: top hub = memory/researcher/INDEX.md (51 out-edges)

## Acceptance criteria status
- ✅ Two consecutive syncs produce updated graph with delta reported
- ✅ No orphans unflagged (orphan_count in output + JSON)
- ⏳ Production verification: next scheduled mirror run (5-min task) will exercise the hook live
- Note: 1105 orphans is expected — most memory/ leaves are standalone notes not cross-referenced

## Supersedes
memory/archivist/kg-auto-update-progress-2026-11-17.md