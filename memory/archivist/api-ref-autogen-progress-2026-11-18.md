# API Reference Auto-Regeneration — Progress (2026-11-18)

## Goal 3: extend gen_api_ref.py + mirror hook

### What was done this pass
1. **gen_api_ref.py extended** with three modes:
   - default (write): regenerate in place, exit 0
   - `--diff`: compare against committed file; report added/removed routes; exit 1 on breaking changes (removed endpoints)
   - `--check`: like --diff but also fails (exit 2) on any drift

2. **Mirror hook** added to memory_mirror.py main() after the KG hook:
   - Runs `gen_api_ref.py --diff` via subprocess (15s timeout, CREATE_NO_WINDOW)
   - Logs result as `api_ref` (clean) or `api_ref_drift: <details>` (breaking change detected)

### Test results
- Write mode: 33 GET + 20 POST routes generated correctly
- Diff clean: exit 0, counts match (33/20 vs 33/20)
- Breaking change detection: added fake `/api/fake-removed` to committed file → detected as `[BREAKING]`, exit 1 ✓
- memory_mirror.py compiles clean with hook present

### Remaining for full closure
- [ ] One test portal edit triggers regeneration + diff in a live mirror cycle (need next mirror run)
- [ ] Verify the log entry appears in memory_mirror.log after a real cycle

### Artifacts
- memory/archivist/gen_api_ref.py (extended, ~130 lines)
- memory_mirror.py (hook at line ~290)
- memory/portal/api-reference.md (regenerated)