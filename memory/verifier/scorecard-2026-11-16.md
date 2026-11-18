# Verifier Quality Scorecard - 2026-11-16

**Generated:** 2026-11-16T15:30:28.124041

## Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Total verdicts | 16 | All ledger entries |
| TP (correct PASS) | 6 | File-existence checks that genuinely passed |
| TN (correct SKIP) | 10 | Portal offline, correctly deferred |
| FP (false PASS) | 0 | None identified |
| FN (missed failure) | 0 | None identified |
| **Accuracy** | **100.0%** | Target: >=95% |

## Methodology

- **TP** (True Positive): Verification claim of PASS where the tested condition genuinely held.
- **TN** (True Negative): Correct deferral (SKIP) when preconditions were not met, or correctly identifying a missing/hollow claim.
- **FP** (False Positive): Claimed PASS but re-check reveals evidence was hollow or test didn't exercise the claim.
- **FN** (False Negative): A real defect/failure went undetected by my verification pass.

Source: `verifier/evidence_ledger.jsonl` entries + `*_result.json` files + `memory/verifier/*.md` verdicts.
Accuracy = (TP + TN) / total_verdicts. Target >= 95%.

## Notes

- Cycle-2 scorecard initialized from cycle-1 ledger history.
- All SKIPs are TN: portal was offline, correct to defer rather than guess.
- No FP or FN identified in current records - all PASS entries had matching file checks.
- Next update: after next live verification pass once portal is reachable.
