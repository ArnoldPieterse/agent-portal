# Index pointer addendum r43 (2026-11-14, Archivist seat) — 2 lines for synthesis/INDEX.md

Closes Scribe's r43 cutoff gap: pointer lines for the r41/r42 leaves were staged nowhere (batch-r40 covers only r31/r36/r38/r40). This file is the hand-off; Orchestrator applies it on White canonical in the same pass as `memory/synthesis/index-pointer-batch-r40.md`.

## Source verification (Archivist seat, this round)
- Target: `memory/synthesis/INDEX.md` = **485a6558 / 2,702 B** — matches Scribe's r43 re-measure exactly; newest pointer line is still the r27 entry, so both lines below are genuinely absent.
- `memory/synthesis/2026-11-14-r42-round-record.md` = **9ebab4c4 / 2,380 B** (present on this seat)
- `memory/synthesis/2026-11-14-r41-closeout.md` = **614f1d9c / 3,051 B** (present on this seat)

## Apply instruction
Insert both lines at the TOP of the pointer list in `memory/synthesis/INDEX.md` (newest-first convention) — i.e. above the batch-r40 lines and above the existing r27 line, in the order given (r42 first).

## The two lines (verbatim)
```
- -> memory/synthesis/2026-11-14-r42-round-record.md   r42 round record (11-14 ~05:4x): 45323d09 candidate = mirror-lag not contradiction (both copies byte-exact on this seat); all six agent lanes closed; TODO.md regression + Archivist audit flags staged for bundle — round record, no supersession
- -> memory/synthesis/2026-11-14-r41-closeout.md   r41 closeout (11-14 ~05:3x): INDEX pointer batch fully staged 4/4 as new file index-pointer-batch-r40.md; handoff chain r31/r36/r38 re-verified byte-exact — round record, no supersession
```

## Notes
- New-file form per transport rule (seat edits to existing INDEX lose the mirror race — proven r16/r18/r23/r24, r25 flag C; same reason Scribe staged batch-r40 as a new file).
- No supersession: both leaves are round records; the supersession-chains footer of INDEX.md is unchanged.
- Owner: Orchestrator (White apply). Adjudication stamp belongs in Arnold's console pass list alongside the TODO.md md5 stamp.
