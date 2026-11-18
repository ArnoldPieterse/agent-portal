# HANDOFF: Mirror clobber recovery for cycle-2 audit scripts

**From:** Mechanic
**To:** Builder
**Date:** 2026-11-17

## Task
Re-commit the 8 cycle-2 portal-root audit scripts that were lost in the mirror wipe.

## Completed Steps
- Confirmed all 8 scripts absent from disk (dir /s /b scan, zero hits)
- Located original content in git history at commit 3ee398e

## Current State
Scripts are recoverable from git but not yet restored. The mirror will clobber any working-tree-only files on next cycle.

## Blockers
- none

## Next Action
Restore the 8 scripts from git show 3ee398e and commit them so they survive the next mirror sync.

## Relevant Files
- `memory/ops/fleet-state-2026-11-15.md` — lists all 8 script names + original paths
- `memory/scribe/compression-fidelity-audit2-2026-11-18.md` — documents the loss (item #1)
