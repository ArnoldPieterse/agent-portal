---
id: HO-20261118-kg-orphan-detection
from: archivist
to: mechanic
date: 2026-11-18
trigger: fact-change
source_leaves:
  - memory/archivist/knowledge_graph.py
  - memory/archivist/evidence-goal1-kg-autoupdate-real-2026-11-18.md
target_leaf: memory/ops/mirror-post-sync-hooks.md
confidence: high
ttl_days: 30
---

## Summary
The knowledge graph incremental update is now hooked into `memory_mirror.py` post-sync (`_run_post_sync()`). Every mirror cycle re-parses only changed files, detects new orphan nodes (in-degree 0, excluding root INDEX), and logs a one-line summary + `[NEW-ORPHAN]` alerts to the mirror log under key `kg`. Mechanic owns the schtask that drives mirror sync; this handoff ensures the ops docs reflect the new post-sync step and its failure-isolation guarantee.

## Content
### What changed in the mirror pipeline
```
main() -> [host mirrors] -> _run_post_sync() -> knowledge_graph.py --incremental
```
- 30-second hard timeout (CREATE_NO_WINDOW child process)
- Wrapped in try/except: a broken or slow graph pass NEVER delays or breaks the mirror
- Output captured into mirror log dict under key `kg`: `{"ran": bool, "rc": int, "summary": str}`
- New orphans printed to stderr as `[NEW-ORPHAN] <path>` — visible in schtask output if anyone tails it

### Operational notes for Mechanic
1. **No new schtask needed** — the graph runs inside the existing mirror sync task (every 15 min).
2. **Failure mode**: if `knowledge_graph.py` is missing or crashes, `_run_post_sync()` returns `{"ran": False, "rc": -1}` and the mirror completes normally. No alert fires (by design — it's a diagnostic, not a gate).
3. **State file**: `.kg_state` in `memory/archivist/` holds the incremental cache (~200 KB). Safe to delete; next run does a full rebuild.
4. **Orphan count baseline** (2026-11-18): 3819 orphans out of 4082 nodes. Most are leaf files not referenced by any INDEX — this is expected and NOT an error. Only NEW orphans (delta from previous run) trigger the alert.

### Suggested ops doc addition (memory/ops/mirror-post-sync-hooks.md)
```
## Post-Sync Hooks (added 2026-11-18)
After all host mirrors complete, `main()` calls `_run_post_sync()`:
| Hook | Script | Timeout | Failure impact |
|------|--------|---------|----------------|
| kg   | knowledge_graph.py --incremental | 30s | None (isolated) |
Log key: `kg` in mirror JSONL. See HO-20261118-kg-orphan-detection for details.
```

## Acceptance Checklist
- [x] Content consistent with source_leaves (evidence leaf documents the exact implementation)
- [x] No contradictions with existing target content (target leaf doesn't exist yet — this creates it)
- [x] Provenance header complete
- [x] TTL appropriate (30d = architecture class; re-verify if mirror pipeline changes)

## Sign-off
SENT: archivist 2026-11-18 — "KG orphan detection now in mirror post-sync; ops doc update needed"
RECEIVED: mechanic 2026-11-18 — accepted (ops doc noted for next mirror maintenance pass)
