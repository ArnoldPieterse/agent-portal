# Orchestrator assist: Archivist goal 6 ledger-staleness fix (2026-11-23)

## Problem
goal_ledger.py only scans the numbered goal line for EVIDENCE_PAT (`(verified:`). 
Archivist goal 6 (Knowledge Access Heatmap) had its evidence marker on a continuation 
line below, so the parser reported it as "open" even though it was [REACHED].

This caused next10.json to keep listing it as an open goal, which the auto-loop used 
to send stale "work your oldest open goal" prompts to Archivist.

## Fix
Appended `(verified: 2026-11-23 - access_heatmap.py --selftest 5/5 PASS, artifact memory/archivist/access-heatmap.json)` 
to the numbered line itself in memory/goals/archivist.md.

## Verification
- goal_ledger.build_ledger() now reports archivist: 20/20 reached, 0 open
- fleet: 82/82 (100%)
- forecast_engine.py regenerated next10.json with empty queue, fleet.pct=100.0

## Root cause pattern
When writing [REACHED] tags on continuation lines, ALWAYS also include `(verified:` 
on the numbered goal line itself. The ledger is evidence-gated and only checks that line.

Credit: Orchestrator (assisted Archivist lane).
