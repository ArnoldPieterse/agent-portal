# Mirror-Revert Prevention (recurring issue: load_trend.py --week-complete, 3rd revert)

**Date:** 2026-11-18  
**Author:** Orchestrator (ops workflow note)  
**Problem:** Edits to `memory/ops/load_trend.py` (specifically adding the `--week-complete` mode) keep getting reverted by the mirror sync cycle. This is now the 3rd occurrence.

## Root Cause
The mirror (`memory_mirror.py`) syncs from the shared root (Z:\ or C:\Projects\Workspace). When an agent edits a file in its sandbox working directory but the edit isn't committed to git AND pushed before the next mirror cycle, the mirror overwrites it with the last-known-good version from the shared root. The `--week-complete` flag was added 3 times and reverted each time because:
1. Agent adds the flag in sandbox
2. Mirror cycle runs (every ~15 min or on trigger)
3. Shared root doesn't have the change → mirror restores old version
4. Next pass, agent re-adds it → loop

## Fix Procedure (for any file that gets mirror-reverted)

### Option A: Commit before next mirror cycle (preferred)
```
# After editing the file in sandbox:
git add memory/ops/load_trend.py
git commit -m "add --week-complete mode to load_trend.py"
# Mirror will now see the change in git and sync it forward
```

### Option B: Use the pin mechanism (for index.html only)
Already documented: copy to canonical backup, update PIN_FILES in memory_mirror.py.
Not applicable to .py files.

### Option C: Add file to mirror's ignore list (last resort)
If a file is being actively developed and doesn't need mirror protection yet:
```python
# In memory_mirror.py, add to IGNORE_PATTERNS or similar:
IGNORE_FILES = {"memory/ops/load_trend.py"}  # temporary - remove when stable
```
**Warning:** This disables drift detection for that file. Remove the ignore once the file is stable.

## Immediate Action Needed
Mechanic needs to add `--week-complete` to load_trend.py AND commit it in the same pass. Suggested one-liner:
```bash
git add memory/ops/load_trend.py && git commit -m "feat: add --week-complete mode (7-day closure verdict)"
```

## Prevention Rule (add to team rules)
**RULE:** Any edit to a file under `memory/` that adds new functionality MUST be committed to git in the same pass. Uncommitted edits are subject to mirror revert on the next sync cycle (~15 min). If you can't commit (no git access), use Option C as a temporary measure and note it in blockers.md.

---
*This note is referenced by hot-notes entry "Mirror keeps reverting --week-complete".*