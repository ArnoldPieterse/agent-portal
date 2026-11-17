# Evidence: Goal #3 - API Reference Auto-Regeneration (progress)

Date: 2026-11-18
Agent: Archivist

## What was done

Extended `memory/archivist/gen_api_ref.py` from cycle-2 (regenerate-only) to cycle-3 with:

1. **--diff mode**: Compares newly parsed routes vs previously committed api-reference.md.
   - Exit 0 = CLEAN (no changes)
   - Exit 1 = DRIFT (new routes added, no removals)
   - Exit 2 = BREAKING CHANGE (endpoints removed)

2. **--check mode**: Like --diff but auto-regenerates api-reference.md when drift detected.
   Suitable for CI gate / pre-commit use.

3. **Pre-commit hook** installed at `.git/hooks/pre-commit`:
   - Triggers on `agent_portal.py` changes in staged diff
   - Runs `gen_api_ref.py --check`
   - Blocks commit on breaking changes (exit 2)
   - Auto-stages updated api-reference.md on drift (exit 1)

## Test results (all passed this session)

| Scenario | Expected | Actual |
|----------|----------|--------|
| Clean state, --diff | exit 0, "CLEAN" | ✓ exit 0 |
| Fake endpoint in old ref, --diff | exit 2, "[BREAKING]" | ✓ exit 2, flagged `/api/fake-removed` |
| Route removed from old ref (simulates new portal route), --diff | exit 1, "DRIFT" | ✓ exit 1, flagged `/api/fleet` as ADDED |
| Drift state, --check | regenerates file, exit 1 | ✓ file regenerated, subsequent --diff shows CLEAN |

## Remaining for full closure

- [ ] One real portal edit (add/remove a route in agent_portal.py) to trigger the pre-commit hook end-to-end
- [ ] Commit with hook active to verify git integration

## Files modified

- `memory/archivist/gen_api_ref.py` - rewritten with --diff/--check modes (4861 bytes)
- `.git/hooks/pre-commit` - new hook script (sh, 755)
- `memory/portal/api-reference.md` - regenerated (33 GET + 20 POST routes)
