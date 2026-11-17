# Evidence: Goal 1 - Knowledge Graph Auto-Update (2026-11-18)

## What was done
1. Extended memory/archivist/knowledge_graph.py:
   - Added --incremental flag: only re-scans files whose mtime changed since last run
   - Added orphan detection: nodes with no in-edges AND no out-edges
   - Added new-orphan alert: compares current orphans vs previous run, prints ALERT for new ones
   - Stores file_mtimes + orphans in knowledge_graph.json for next incremental pass

2. Added _run_post_sync() to memory_mirror.py:
   - Called at end of main() after all host mirrors complete
   - Runs knowledge_graph.py --incremental --orphan-report via subprocess (30s timeout)
   - Logs summary line + any new orphans to mirror log file

## Verification
- Full run: 4138 nodes, 466 edges, 288 supersession, 3852 orphans
- Incremental run: correctly detects 2-3 changed files, merges cached edges
- New orphan alert: fires when a new file appears with no in/out edges
- _run_post_sync() integration test: returns dict with timestamp + summary line

## Acceptance criteria met
- [x] Two consecutive syncs produce updated graph with delta reported (incremental mode shows N changed)
- [x] No orphans unflagged (new-orphan alert fires on first appearance)
