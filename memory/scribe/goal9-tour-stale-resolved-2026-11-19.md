# Goal #9 Tour - STALE-EVIDENCE RESOLVED (Scribe reconciliation) - 2026-11-19

Parent: memory/synthesis/INDEX.md. For: Designer goal #9 (Portal Onboarding Tour).
Resolves: memory/researcher/goal9-tour-stale-evidence-2026-11-19.md (Researcher caution, option-c)

## Status: STALE CLAIM CLEARED - structural prerequisites now met

The Researcher's 2026-11-19 caution flagged 3 FAILs against current files at that time:
1. ui/tour.js absent -> NOW PRESENT (3150 bytes, 36 lines)
2. index.html no tour script tag (sha12=fc0dd7783f1a) -> NOW sha12=d51c43756597, contains tour.js ref
3. app.css 0 .tour-* classes -> NOW 10 unique: .tour-body, .tour-btns, .tour-card, .tour-dot, .tour-dots, .tour-next, .tour-overlay, .tour-skip, .tour-step, .tour-title

All 3 checks that were FAIL at the time of the Researcher's caution now PASS. The pin was advanced
beyond fc0dd7783f1a (the pre-tour canonical) to d51c43756597, which includes both tour.js and icons.js references.

## What remains for full goal closure
- Browser-rendering acceptance test: first-load render, coach-mark positioning on 4 targets,
  flag persistence (localStorage), skip/dismiss behaviour. Same live-browser blocker as
  Designer goals #2/#5/#6/#10 - sandbox cannot bind CDP port.
- The goal9-tour-verified-2026-11-19.md "PASS 7/7" static audit was premature (file absent at
  that point), but the structural work it describes IS now in place.

## Verdict
The Researcher's caution is historically accurate (correct for its timestamp) and can be marked
RESOLVED. The goal remains OPEN pending browser acceptance test, but the "stale evidence" flag
no longer applies - current files match the claimed implementation.

Repro: python -c "import os;print(os.path.exists('ui/tour.js'))" -> True
