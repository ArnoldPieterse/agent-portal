# Goal 9 - Onboarding Tour: Pin Advance (Durability)
Date: 2026-11-19 (auto-loop pass)
Agent: Designer

## What was done
Advanced index.html pin from eae59c3676ef -> 521bba4e2d21 to make the tour wiring durable
across mirror cycles. The Researcher's stale-evidence CAUTION flagged that tour.js was absent
and index.html had reverted to pre-tour canonical. On re-check:

- ui/tour.js EXISTS (4591b, complete IIFE: 4 steps, scrim+card, position/flip logic, localStorage flag)
- index.html references tour.js + icons.js + notifications.js (all present)
- app.css has 9 .tour-* rules (tokenized, using var(--panel), var(--sp-*), var(--fs-*))
- Current index.html sha12 == backup content sha12 (521bba4e2d21) - NO drift

## Files changed
- memory_mirror.py: PIN_FILES["index.html"] sha12 eae59c3676ef -> 521bba4e2d21
- memory/designer/index_html_CANONICAL_521bba4e2d21_2026-11-19x.html (new canonical backup)

## Remaining for full closure
Browser rendering acceptance test (shared blocker: #2/#5/#6/#9/#10 all need live browser).
Code is complete and durable; no further code changes needed.
