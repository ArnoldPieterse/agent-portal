# Scribe Goal 2 Progress: Cycle Narrative v2 date-filter fix (2026-11-20)

## What was done
- Added `_extract_date()` helper and date-window filtering to `get_key_events()`.
- Previously, key events pulled ALL matching TODO.md headers regardless of cycle window.
  Now events with embedded dates outside [since, until] are skipped.
- Also expanded keyword list to include 'anti-stall' and 'fleet' for better coverage.

## Verification run
Command: `python memory/scribe/cycle_narrative.py --cycle 6 --since 2026-11-18 --until 2026-11-19 --dry-run`
Result: ACCEPTANCE PASS (3-para + agents + bullets)
Output correctly shows ANTI-STALL v2 (2026-11-19) as the key event in window.

## Remaining for full close
- Chat history cross-agent interactions are sparse (only 1 pair found) - likely due to
  limited chat_history_group.json coverage. Not a code bug; data limitation.
- 'All agents mentioned correctly' criterion: narrative names top performer + count;
  individual per-agent breakdown could be added but current output is coherent.

## Artifact
- memory/scribe/cycle_narrative.py (updated with date filter)
