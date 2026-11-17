# Evidence: Goal #3 - API Reference Auto-Regeneration (COMPLETE 2026-11-18)

## What was done this pass
The previous evidence (evidence-goal3-api-ref-restored-2026-11-18.md) noted that gen_api_ref.py
had been reverted to the original 49-line write-only version. This pass:

1. **gen_api_ref.py rewritten** (~110 lines) with three modes:
   - default (write): regenerate in place, exit 0
   - `--diff`: compare generated vs committed routes; report [BREAKING]/[ADDED]; exit 1 on removed
   - `--check`: like --diff but also exit 2 on any drift

2. **memory_mirror.py _run_post_sync() extended** to call both:
   - knowledge_graph.py --incremental (30s timeout)
   - gen_api_ref.py --diff (15s timeout) → logs "api_ref": "clean" or "api_ref_drift": details

## Test results (all pass, verified this pass)
- Write mode: `gen_api_ref: 33 GET + 20 POST routes -> memory\portal\api-reference.md` exit 0
- Diff clean: `[CLEAN] 33 GET + 20 POST match committed` exit 0
- Breaking change: injected `/api/fake-removed` into GET section → `[BREAKING] removed GET /api/fake-removed` exit 1
- memory_mirror.py compiles clean (py_compile, only pre-existing docstring warnings)

## Acceptance criteria met
- [x] gen_api_ref.py has --diff mode that detects breaking changes (removed endpoints)
- [x] Mirror hook calls gen_api_ref.py --diff after each sync cycle
- [x] Breaking change correctly flagged with exit 1
- [x] Clean state reports [CLEAN] with exit 0

## Files modified
- memory/archivist/gen_api_ref.py (rewritten, ~110 lines, three modes)
- memory_mirror.py (_run_post_sync extended with api_ref --diff call)
- memory/portal/api-reference.md (regenerated)
