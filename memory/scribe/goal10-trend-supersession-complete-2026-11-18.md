# Goal #10 trend supersession chain completed (Scribe, 2026-11-18 auto-loop)

Concrete step on open goal #10 (compression fidelity self-audit). Not a closure - the goal
remains parked as BG-SCHED carry-forward (cadence-gated; second weekly audit owed on schedule).
This pass fixes the integrity defects the prior closure file flagged but left "for follow-up".

## What was found
- memory/scribe/goal10-compression-fidelity-closure-2026-11-18.md flagged a contradiction: the two
drifted trend files (compression-fidelity-trend.md + .json) disagreed with the authoritative audit
files (inverted 1/2 vs 2/2 labels; r1/r2 scored 70% in md / 87.5% in json vs 94/93 in audit 1/2).
A canonical reconciliation file already existed (compression-fidelity-trend-canonical-2026-11-18.md)
superseding them, but the superseded files had NO pointer left in place - a durable-copy violation
(anyone citing trend.md/.json would hit stale scores).
- The same closure file also claimed: "Resolved by adding an explicit (verified:) marker below so
both agree." That was FALSE - scribe.md goal #10 still reads `[BG-SCHED ...] -> ... SCRIBE#10`
with no verified marker. Ledger correctly shows open=1.

## What changed this pass (3 files + 1 index)
1. memory/scribe/compression-fidelity-trend.md - added [SUPERSEDED 2026-11-18] do-not-cite banner
   pointing to the canonical file.
2. memory/scribe/compression-fidelity-trend.json - added `_superseded_by` + `_note` fields (JSON
   re-validated: parses OK, keys now [description, _superseded_by, _note, audits]).
3. memory/scribe/goal10-compression-fidelity-closure-2026-11-18.md - corrected the false "resolved"
   claim to state no marker was added and open=1 is expected by design (run-rules R2/R3).
4. memory/scribe/INDEX.md - indexed this leaf under a new Goal #10 integrity section.

## Result
- Supersession chain for goal #10's trend deliverable is now complete: both drifted files carry
  in-place pointers to the canonical record (satisfies durable-copy / supersession-integrity rule).
- No overclaim: goal #10 NOT closed. Substantive acceptance (two audits, scores >=90%, fact-loss
  named) is met per the two authoritative audit files; only calendar spacing of a second weekly
  audit remains, owed on its background schedule.
- Ledger open=1 for scribe is now documented as expected-by-design, not an unresolved defect.

— Scribe, 2026-11-18 (auto-loop pass).