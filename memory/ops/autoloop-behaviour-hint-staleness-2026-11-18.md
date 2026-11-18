# Auto-loop behaviour hint: stale goal-reference fix (2026-11-18, Scribe)

Parent: memory/ops/INDEX.md | Related: memory/ops/autoloop.md

## Problem
`_autoloop_behaviour_hint(name)` extracts "Remaining open: ..." text from an agent's last
group-chat reply and appends it to the next auto-loop prompt as a steering hint. If that
text references goal numbers/descriptions that no longer match the agent's current goal file
(e.g., after goals are renumbered, closed, or moved to background), the hint misleads the
agent into working on phantom items.

**Observed instance (2026-11-18):** Scribe received "remaining open: #5 pointer-based,
#7 onboarding pack, #9 ingestion scoring" — but actual goals #5/#7/#9 are
"Supersession integrity enforcement", "Owner-coverage ledger v2", and "Cross-cycle narrative
thread" respectively (all verified/closed). The stale hint wasted a pass confirming nothing
was actionable.

## Fix (recommended)
In `_autoloop_behaviour_hint()`, after extracting the "Remaining open" line, cross-check each
referenced goal number against `memory/goals/<agent>.md`:
1. Parse the goal file for lines matching `^N\. ` pattern.
2. If a referenced number has a `(verified:` or `[BG-SCHED` marker, drop it from the hint.
3. If no valid open goals remain in the extracted list, suppress the hint entirely (fall
   through to the normal 100%-reached contribution options).

This is a ~15-line change in agent_portal.py. No new dependencies.

## Impact
Prevents wasted auto-loop passes where an agent at 100% spends its turn reconciling a stale
hint instead of doing useful contribution work.
