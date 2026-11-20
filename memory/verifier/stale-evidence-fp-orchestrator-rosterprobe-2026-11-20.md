# Stale-Evidence False Positive — orchestrator.md:17 (rosterprobe path)

**Date:** 2026-11-20
**Status:** FALSE POSITIVE — closed, no action needed.

## Finding

`stale-evidence-2026-11-20.md` flagged `memory\goals\orchestrator.md:17` as missing
evidence at path `memory/rosterprobe/INDEX.md`.

**Verification:**
- `memory/rosterprobe_archived_2026-11-20/INDEX.md` EXISTS (confirmed on disk).
- Line 17 of orchestrator.md references the CORRECT archived path:
  `memory/rosterprobe_archived_2026-11-20/INDEX.md`.
- No occurrence of the unarchived path `memory/rosterprobe/INDEX.md` exists in the file.

## Root Cause

The freshness audit script's evidence-path extractor likely parsed the agent name
"RosterProbe" or the goal-file ref "goals/rosterprobe.md" and constructed a false
evidence path `memory/rosterprobe/INDEX.md`. The actual verified marker text is correct.

## Resolution

No file edit needed. Marking as closed (false positive). The underlying claim
(onboard+retire round-trip PASS) remains valid with correct archived-path citation.
