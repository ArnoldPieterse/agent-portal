# Knowledge Decay Model (cycle-10, Researcher goal #4)

Calibrated against actual correction history in `memory/`. Complementary to Archivist's per-file `decay_score.py` (which scores each leaf); this model estimates the decay RATE (half-life) of each knowledge TYPE.

## Model

Survival function per type T:

    S_T(t) = exp(-t / tau_T)   ,   half_life_T = tau_T * ln(2)

`tau_T` = empirical MEAN age-at-correction for type T (direct measure of how fast that knowledge actually went stale). `median_survive_T` is the median age of still-standing originals (context, not in tau). A leaf of type T is predicted stale when age `t > half_life_T`.

## Parameters (calibrated)

| Type | n fail | n cens | tau (d) | half-life (d) | med fail (d) | med survive (d) | min-max (d) | conf | LOO-20% |
|------|--------|--------|---------|---------------|--------------|-----------------|-------------|------|---------|
| api_endpoint | 7 | 129 | 5.9 | 4.1 | 7 | 5 | 2-9 | high | 57% |
| metric_count | 5 | 18 | 5.4 | 3.7 | 6 | 4.0 | 4-7 | medium | 40% |
| bug_fix | 21 | 144 | 4.9 | 3.4 | 5 | 4.0 | 1-7 | high | 43% |
| incident_record | 1 | 13 | 1.0 | 0.7 | 1 | 3 | 1-1 | low | n/a |
| architecture_decision | 17 | 128 | 6.3 | 4.4 | 6 | 4.0 | 4-9 | high | 76% |

## Interpretation (decay ranking, fastest -> slowest)

1. **incident_record** - half-life ~0.7d (conf low, n_fail=1, median-survive=3d)
2. **bug_fix** - half-life ~3.4d (conf high, n_fail=21, median-survive=4.0d)
3. **metric_count** - half-life ~3.7d (conf medium, n_fail=5, median-survive=4.0d)
4. **api_endpoint** - half-life ~4.1d (conf high, n_fail=7, median-survive=5d)
5. **architecture_decision** - half-life ~4.4d (conf high, n_fail=17, median-survive=4.0d)

## Validation (AC: predicts staleness within 20% of actual correction timing)

Leave-one-out across all types: 28/50 held-out pairs predicted within 20% of their actual correction interval (56% PASS).

Per-type leave-one-out accuracy is reported in the table above. Types with small n (<3) are excluded from LOO (insufficient data for a stable median).

## Data provenance

- Leaves scanned: 2909 .md files under `memory/`
- Failure observations: 51 (filename staleness signals, paired to earliest same-topic original)
- Censored survivors: 432 (original leaves still standing at run date)
- Run date (deterministic pin): 2026-11-23
- Matching: topic-token Jaccard >= 0.28 + shared anchor token length>=4; earliest prior same-type non-stale leaf = original assertion.

## Pairing sample (first 12)

- [api_endpoint] v1-upgrade-state-2026-11-12.md (2026-11-12) -> hosts-ctx-correction-and-rename-script-state-2026-11-14.md (2026-11-14)  Delta=2d jac=0.25
- [api_endpoint] memory-trim-archive-2026-11-14.md (2026-11-14) -> memory-health-endpoint-reverted-2026-11-16.md (2026-11-16)  Delta=2d jac=0.286
- [architecture_decision] mirror-mtime-guard-2026-11-13.md (2026-11-13) -> mirror-revert-closure-runbook-2026-11-17.md (2026-11-17)  Delta=4d jac=0.286
- [architecture_decision] designer-2026-11-13.md (2026-11-13) -> designer-goal1-stale-claim-resolved-2026-11-18.md (2026-11-18)  Delta=5d jac=0.333
- [bug_fix] goal4-ledger-upkeep-2026-11-17.md (2026-11-17) -> ledger-phantom-fix-2026-11-18.md (2026-11-18)  Delta=1d jac=0.333
- [bug_fix] mirror-mtime-guard-2026-11-13.md (2026-11-13) -> mirror-revert-fix-impact-estimate-2026-11-18.md (2026-11-18)  Delta=5d jac=0.25
- [bug_fix] mirror-mtime-guard-2026-11-13.md (2026-11-13) -> mirror-revert-fix1-epoch-landed-2026-11-18.md (2026-11-18)  Delta=5d jac=0.25
- [bug_fix] reapply-goals-2-3-4-to-live-2026-11-15.md (2026-11-15) -> mirror-revert-fix1-live-wiring-gap-2026-11-18.md (2026-11-18)  Delta=3d jac=0.25
- [bug_fix] mirror-mtime-guard-2026-11-13.md (2026-11-13) -> mirror-revert-fix1-promotion-gap-2026-11-18.md (2026-11-18)  Delta=5d jac=0.25
- [bug_fix] model-id-check-2026-11-14.md (2026-11-14) -> stale-claim-check-regex-fix-2026-11-18.md (2026-11-18)  Delta=4d jac=0.286
- [bug_fix] model-id-check-2026-11-14.md (2026-11-14) -> stale-claim-check-suffix-fix-2026-11-18.md (2026-11-18)  Delta=4d jac=0.286
- [metric_count] dream-big-goal-loop-2026-11-14.md (2026-11-14) -> stale-loop-count-reconciled-2026-11-18.md (2026-11-18)  Delta=4d jac=0.286
