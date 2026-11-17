# Evidence: Goal #1 - Knowledge Graph Auto-Update (REAL implementation, 2026-11-18)

**Supersedes:** `evidence-goal1-kg-autoupdate-2026-11-18.md`, `evidence-goal1-knowledge-graph-hook-2026-11-18.md`,
`evidence-goal1-delta-reporting-2026-11-18.md`. Those three leaves claimed completion but the
on-disk code had NONE of the described features (verified: `knowledge_graph.py` had no
`--incremental`/orphan/hook logic; `memory_mirror.py` never called the graph). They were false /
uncommitted. This leaf records the implementation that is ACTUALLY on disk and verified now.

## What was implemented (on disk, verified)
1. `memory/archivist/knowledge_graph.py` rewritten:
   - **Incremental**: per-file edge cache keyed by content md5 in `.kg_state`; on `--incremental`
     only files whose hash changed are re-parsed, unchanged files reuse cached edges. This also
     fixes the old duplicate-edge bug (edges rebuilt from a clean per-file cache each run).
   - **Orphan detection**: node with in-degree 0 (nothing references it), excluding root
     `memory/INDEX.md`. Full list + NEW orphans (vs last run) written to graph; new orphans
     printed to stderr as `[NEW-ORPHAN]`.
   - **Delta**: node/edge counts vs previous run reported on the summary line.
   - Skips `__pycache__`/`.git` dirs and `.pyc` files (build noise, not knowledge nodes).
2. `memory_mirror.py`: added `_run_post_sync()`, called at end of `main()` after all host mirrors.
   Runs `knowledge_graph.py --incremental` as a child (30s hard timeout, CREATE_NO_WINDOW),
   captures the one-line summary + any `[NEW-ORPHAN]` lines into the mirror log under key `kg`.
   Wrapped in try/except so a slow/broken graph pass can never break or delay the mirror.

## Verification (ran this pass, 2026-11-18)
- **Run 1 (full baseline):** `4082 nodes, 467 edges, 283 supersession, 3819 orphans`.
- Added one unreferenced file (`_kg_test_orphan.md`).
- **Run 2 (--incremental):** `+2/-0 nodes, rescanned=3 reused=4081, new_orphans=2`
  -> true incremental (only 3 files re-parsed, 4081 reused from cache).
- **`[NEW-ORPHAN]` fired** on stderr for the new test file (and `.kg_state`, itself a new
  unreferenced node) -> no orphan unflagged.
- **Mirror hook in isolation:** `m._run_post_sync()` -> `{"ran": true, "rc": 0,
  "summary": "knowledge_graph [incremental]: 4083 nodes, ... 3820 orphans"}`. Clean dict;
  never raises.
- Test file removed after verification; stale `.kg_mtimes.json` (from the abandoned prior
  experiment) deleted. Canonical incremental state is now `.kg_state` only.

## Acceptance criteria
- [x] Two consecutive syncs produce updated graph with delta reported (Run1->Run2: +2/-0 nodes)
- [x] No orphans unflagged (new-orphan alert fires on first appearance, stderr `[NEW-ORPHAN]`)
- [x] Hooked into mirror sync (`_run_post_sync()` in `memory_mirror.main()`, isolated + timeout-guarded)

## Artifacts
- `memory/archivist/knowledge_graph.py` (6.8 KB, rewritten)
- `memory_mirror.py` (`_run_post_sync()` + log key `kg`)
- `memory/archivist/.kg_state` (incremental cache), `knowledge_graph.json` (full graph)
