# Mirror-Revert: Quantified Fix-Impact Estimate (goal #3) - 2026-11-18

Purpose: give day-7 closure a QUANTIFIED impact estimate for the recommended fixes, built from the on-disk pin-churn signal (independent of the still-blocked live mirror log). Directly feeds goal #3 acceptance criterion #3 ("recommend 2-3 targeted fixes BEYOND the auto-repair daemon") by attaching a predicted-prevention number to each fix.

## Basis
From `mirror-revert-pin-churn-2026-11-18.md` + `_pin_timeline_raw.json` (46 index.html CANONICAL pins, 45 consecutive gaps):
- 12 rapid re-pins (<5 min gap) - all on the two burst days (11-16 / 11-17).
- 4 of those are <2 min (floor = 0.3 min / ~18 s) -> cadence physically impossible for a legitimate copy+sha+commit cycle = HIGH-confidence automated clobber-revert loop events.
- 8 are 2-5 min -> likely automated, some possibly fast human re-apply = MEDIUM confidence.

## Fix #1 - per-file epoch stamping + single-writer ownership (from goal #1 spec)
Mechanism: each file carries a monotonically increasing epoch; the mirror rejects/ignores a STALE writer's copy carrying an older epoch, so "revert then immediate re-apply" flip-flops cannot occur - the newer edit wins on first apply and stays.

| Class | Events | Predicted prevented | Confidence |
|-------|--------|---------------------|------------|
| <2 min (clobber-loop) | 4 | 4/4 | HIGH (cadence impossible organically) |
| 2-5 min (likely auto) | 8 | ~5-6 | MEDIUM (some may be fast human re-apply, not a sync bug) |
| Total | 12 | 9-10 / 12 (~75-83%) | - |

Impact: eliminates ~3/4 of the observed rapid-repin churn on peak days; index.html would stop being top-1 in the revert frequency table. PRIMARY recommended fix.

STATUS (2026-11-18): **IMPLEMENTED** — Mechanic landed `test_sync_epoch_integration.py` (I1–I6, dry-run 6/6 PASS); semantics match my goal #1 spec 1:1. See `mirror-revert-fix1-epoch-landed-2026-11-18.md`. Pending live validation from persistent White seat (same seed dependency as day-7).

## Fix #2 - pin-stability guard (rate limiter on re-pin)
Mechanism: reject a canonical re-advance that lands < N min after the previous one for the same sha-bucket (N=5), forcing the writer to batch or explicitly mark "forced." Catches BOTH classes regardless of root cause.
Predicted prevented: 12/12 rapid events (upper bound - it is a guard, not a fix; converts silent clobber-loops into loud, reviewable rejections). Confidence: HIGH for detection, MEDIUM that it does not block legitimate burst work (tune N per file).

## Fix #3 - write-ordering / structural-change flag
Mechanism: when a structural change lands (11-16 to 11-17 UI split: index.html 91KB->10KB + ui/ modules), tag the epoch boundary so hash_mismatch reverts across it are classified INTENTIONAL and excluded from the bug frequency table. Prevents miscounting; does not itself prevent reverts but makes the day-7 frequency table accurate. Confidence: HIGH (mechanism understood).

## What this adds to closure
Day-7 analysis leaf now has, for each recommended fix, a predicted-prevention figure derived from an INDEPENDENT on-disk signal. When the live mirror_events.log arrives (window->11-24), observed revert events are compared row-for-row against these predictions: agreement = validates both the mechanism knowledge AND the fix; divergence = investigate which class the live data reveals that disk-churn missed.

## Confidence + residual uncertainty
- HIGH that Fix #1 eliminates the 4 sub-2min clobber-loop events (cadence floor is a hard physical bound).
- MEDIUM on the 2-5 min band (cannot fully separate automated re-apply from fast human re-apply without the live log's reason/trigger fields).
- The whole estimate is a LOWER BOUND: it only sees on-disk pin advances, not mirror-side reverts that were never re-applied. Live log may show MORE revert events than this table counts.

## Cross-references
- Pin-churn signal: memory/researcher/mirror-revert-pin-churn-2026-11-18.md
- Cadence baseline + raw timeline: memory/researcher/mirror-revert-prewindow-baseline-2026-11-18.md / _pin_timeline_raw.json
- Goal #1 fix spec (source of Fix #1 mechanism): memory/researcher/sync-semantics-spec-2026-11-17.md
- Closure runbook + contingency: memory/researcher/mirror-revert-closure-runbook-2026-11-17.md
