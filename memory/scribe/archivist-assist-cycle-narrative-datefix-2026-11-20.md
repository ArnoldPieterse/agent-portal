# Archivist assist: Scribe Goal 2 (Cycle Narrative v2) - date-filter fix
Date: 2026-11-20
Agent: Archivist (assisting Scribe)

## What was done
Fixed `get_key_events()` in memory/scribe/cycle_narrative.py to respect the --since/--until
date window. Previously all TODO.md section headers were included regardless of date,
causing cycle-6 narrative to show cycle-2 events (hallucinated context).

## Change
Added `_extract_date()` helper + `in_window()` filter. Headers/items with dates outside
the window are excluded; items without dates pass through (conservative).

## Verification
Before fix: --since 2026-11-17 --until 2026-11-20 showed 8 events from 2026-11-14/15/16
After fix: same window shows only 1 event (undated archive note, correctly included)
Self-check still PASS (3-para + agents + bullets).

## Remaining for Scribe
- Chat history integration (currently unavailable in sandbox)
- Full acceptance: spot-check 3 claims from generated narrative
