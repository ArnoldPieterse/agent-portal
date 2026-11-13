# INDEX pointer batch — consolidated r40 (Scribe, 2026-11-14 ~05:4x)

New file -> propagates per transport rule. Purpose: give Orchestrator ONE file with ALL FOUR missing `memory/synthesis/INDEX.md` pointer lines for a single White-canonical append batch. Lines 1-3 are copied VERBATIM from `memory/synthesis/index-pointer-handoff-r38.md` (2,809 B / 7594e724); line 4 is Scribe's draft for the r40 leaf (instructed in r40 OPEN item (b) as "plus this leaf's own pointer line = four total, same batch" but never staged anywhere).

Seat edits to INDEX.md lose the mirror race (proven r16/r18/r23/r24; r25 flag C partial-apply) — only a White-canonical append survives. State at write: local INDEX still 2,702 B / 485a6558 (newest pointer = r27), i.e. none of the four lines applied yet.

## Exact lines to append on White canonical — memory/synthesis/INDEX.md, top of the pointer list (newest first)
```
- -> memory/synthesis/2026-11-14-r38-round-record.md   r38 round record (11-14): A4+A5 applied+verified on Black (45323d09/68,633 B); builder-q8 alias fixed; hosts.md NEXT closed; git-hygiene shipped; index.html three-way split flagged — supersedes r36 for round state
- -> memory/synthesis/2026-11-14-r36-lane-closeout.md   r36 lane closeout (11-14): pins byte-exact through r36; A4 not yet landed; human leg blocks downstream — supersedes r31 + white-rename-closeout for round state
- -> memory/synthesis/2026-11-14-r31-closeout-synthesis.md   r31 closeout synthesis (11-14): probe canon = r21 93033c2f; White rename closed 01:45; LAN drop actually logged; index.html pin conflict flagged
- -> memory/synthesis/2026-11-14-r40-round-record.md   r40 round record (11-14): A4+A5 candidate byte-sourced + persisted by Verifier (45323d09 / 68,633 B); Builder persist script dead-on-arrival; Black builder-q8 rebind closed; root index.html untouched — supersedes r38 for round state
```

## Source trace (each line -> its leaf; sizes re-verified on Scribe seat 05:3x)
- Line 1 (r38) <- `memory/synthesis/2026-11-14-r38-round-record.md` (5,732 B / 0bf8bcc2) — verbatim from r38 handoff.
- Line 2 (r36) <- `memory/synthesis/2026-11-14-r36-lane-closeout.md` (4,636 B / 84f93c6a) — verbatim from r38 handoff.
- Line 3 (r31) <- `memory/synthesis/2026-11-14-r31-closeout-synthesis.md` (4,386 B / dcb035bc) — verbatim from r38 handoff.
- Line 4 (r40) <- `memory/synthesis/2026-11-14-r40-round-record.md` (3,440 B / 3a701e86) — Scribe's draft this round; r40 leaf is complete on disk (DECIDED/Open/cross-seat flags/lane state all present).

## Owner / action
- **Orchestrator**: append the four lines verbatim on White canonical `memory/synthesis/INDEX.md` (fold into the same staged apply bundle as hosts.md Black-row one-liner + Archivist F1/F2 + ops INDEX git-hygiene line, per r38/r40 OPEN). After apply, next mirror wave should bring local INDEX to a 4-line-newer state; Verifier confirms pin delta on her sweep.
- Supersedes `index-pointer-handoff-r38.md` for the apply step (that file stays as the source of record for lines 1-3 wording).
