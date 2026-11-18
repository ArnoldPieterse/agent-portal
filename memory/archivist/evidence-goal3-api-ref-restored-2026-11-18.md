# Evidence: Goal #3 - API Reference Auto-Regeneration (2026-11-18, pass 2)

## Problem discovered
Previous progress doc (api-ref-autogen-progress-2026-11-18.md) claimed both gen_api_ref.py
extensions AND mirror hooks were in place. On inspection:
- gen_api_ref.py was reverted to original 49-line version (no --diff/--check modes)
- memory_mirror.py had NO post_sync hooks at all (kg or api_ref)
- The earlier evidence was from a file state that did not persist

## What was done this pass
1. **gen_api_ref.py rewritten** (129 lines) with three modes:
   - default (write): regenerate in place, exit 0
   - `--diff`: compare generated vs committed; report added/removed routes; exit 1 on breaking
   - `--check`: like --diff but also fails (exit 2) on any drift

2. **memory_mirror.py extended** with `_run_post_sync()` function:
   - Runs `knowledge_graph.py --incremental` (30s timeout) after each mirror cycle
   - Runs `gen_api_ref.py --diff` (15s timeout) after KG check
   - Results logged under `"post_sync"` key in memory_mirror.log

## Test results (all pass)
- Write mode: 33 GET + 20 POST routes generated -> memory/portal/api-reference.md
- Diff clean: `[CLEAN] 33 GET + 20 POST match committed`, exit 0
- Breaking change: injected fake `/api/fake-removed` into committed file ->
  `[BREAKING] removed GET /api/fake-removed`, exit 1 (correct)
- memory_mirror.py compiles clean (py_compile, only pre-existing docstring warnings)

## Remaining for full closure
- [ ] Next live mirror cycle must show `"post_sync": {"kg": ..., "api_ref": ...}` in memory_mirror.log
  (hook is in place; will fire on next scheduled run)

## Files modified
- memory/archivist/gen_api_ref.py (rewritten, 129 lines)
- memory_mirror.py (_run_post_sync added at line 270, called in main at line 311)
