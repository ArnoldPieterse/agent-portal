# Builder r38 - A4+A5 lineage proof + seat-revert evidence (2026-11-14)

## Timeline
- 06:05:5x: hash-gated `apply_a4_a5_r35.py` ran from this seat on root index.html (gate = 9c6b08e3/67,681 PASS). Pre-apply backup preserved as `index.html.pre-a4a5-r35.bak` (script itself makes no bak; the .bak naming + mtime-preservation pattern is from a manual pre-copy).
- Verifier r38 measured the result on their seat: 68,633 B / 45323d09 - VERIFIED byte-exact vs backup.

## First-party lineage proof (this round)
- In-memory re-application of the exact transform from `.bak` reproduces **68,633 B / md5 45323d09717ac3a9dc0e098015863d81** - byte-exact with Verifier's measurement. Full 32-char md5 now on record (prior pins carried only the 8-char prefix).
- `a4a5_sim_out.html` (a22ec518/68,634, mtime 05:40) is a SUPERSEDED draft: first diff vs final at byte 2459 (#modeBar still lacks position:relative - predates final A4-B css hunk). Do NOT pin to it.

## Seat state + revert evidence
- My seat root index.html is back at 9c6b08e3/67,681 with ORIGINAL mtime 11-13 23:03:00 preserved -> the applied file was reverted by a White-canonical mirror pass (White still un-stamped; stamp = Arnold's human console leg).
- Designer r31 reading 9c6b08e3 = post-revert state; Verifier r38 reading 45323d09 = pre-revert. Both correct in time; no contradiction about the apply itself.

## Ruling (Builder)
- Do NOT re-apply to root from any remote seat: 07:5x ruling stands, and a re-apply would just revert again on the next mirror pass (churn + SKEW_SUSPECT risk).
- Close path: Arnold's console pass stamps **45323d09717ac3a9dc0e098015863d81 / 68,633 B** as canonical on White -> mirror converges all seats -> Designer re-runs sheet against the new fingerprint (r19 FAILs #3/#4/#5 already fixed in code per Verifier r38).

## Pins from this seat (this round)
- memory/llm/hosts.md: 2f5aafe3 / 16,455 B - matches Orchestrator 08:0x pin
- agents.json: **b8b033d5** / 9,571 B - DISCREPANCY vs Orchestrator 08:0x pin 2d5433db (same size, content differs). No local copy of the pinned version to diff against; adjudicable only by White-side md5. ADD TO ARNOLD'S WHITE SWEEP LIST.
