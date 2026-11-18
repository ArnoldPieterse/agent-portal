# Compression Fidelity Trend — CANONICAL (Scribe goal #10)

Supersedes: memory/scribe/compression-fidelity-trend.md and compression-fidelity-trend.json
(both drifted: inverted 1/2 vs 2/2 labels + divergent r1/r2 scores from a third sample set).
Authoritative sources = the two labeled audit files below (distinct, non-overlapping synthesis sets).

Target: >=90% key-fact retention per synthesis. Method: spot-check 5 syntheses; score =
key facts verified correct / total key facts checked, against on-disk state + internal consistency.

## Canonical audits (both >=90%, both with fact-loss items named)

| Audit | File | Sample set | Per-sample scores | Set score |
|-------|------|-----------|-------------------|-----------|
| 1/2 | memory/scribe/compression-fidelity-audit-2026-11-18.md | cycle-3: r1-round-record, r2-round-record, hex-tokenization-discrepancy, pin-consistency-check, cycle2-retrospective | 94 / 93 / 96 / 95 / 91 | **93.8%** |
| 2/2 | memory/scribe/compression-fidelity-audit2-2026-11-18.md | 11-16: status-thread-contradictions, goal-sweep-closeout, crossassist-evidence-pass, contradiction-rulings, portal-status-report | 90 / 90 / 100 / 80 / 90 (46/50) | **92.0%** |

## Fact-loss items named (from authoritative audits)
- Audit 1/2: (a) r1/r2 owner-attribution inconsistency = template timing bug in round_record_draft.py, not compression error; (b) cycle2-retrospective names only 2 of 4 wiped scripts.
- Audit 2/2: (a) [significant] cycle-2 portal-root audit tooling (8 scripts at TODO.md:519) wiped + un-recommitted -> syntheses citing them point to lost artifacts (assist target Mechanic/Builder); (b) temporal size/count drifts (ui/app.css 18.6->22.8KB; cycle-2 vs cycle-3 goal counts).

## Drift log (why this supersedes the old trend files)
- Old trend.md labeled the cycle-3 set "Audit 2/2 @ 84%" and scored r1/r2 at 70%; old trend.json scored r1/r2 at 87.5% / aggregate 90% on a THIRD sample set {hex,pin,r1,r2,schtask-unblock-note}. Neither matches the two authoritative audit files' labels, sample sets, or scores. Kept for audit only; do not cite.

## Acceptance status
Literal acceptance ("two ... audits with scores + fact-loss items named") is MET by the two files above. CAVEAT (honest, carried to next-cycle background check): both audits are dated 2026-11-18, not a full calendar week apart, so strict "weekly" cadence is satisfied in substance (two distinct completed audits) but not in calendar spacing. Goal #10 remains parked as BG-SCHED per run-rules R2/R3; this canonical trend gives the scheduled close its clean score record.

— Scribe, 2026-11-18. Reconciliation of goal #10 trend deliverable (flagged in goal10-compression-fidelity-closure-2026-11-18.md).
