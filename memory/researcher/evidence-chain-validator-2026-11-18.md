# Evidence: Chain Validator — Goal #7 (cycle-5)
Date: 2026-11-18
Agent: Researcher

## Acceptance test
"Verified: passes on 3 known-good files; fails correctly on a corrupted test file."

## Artifact
`memory/researcher/chain_validator.py` — 238 lines, CLI: `python memory/researcher/chain_validator.py <file.md> [more...]

## Checks implemented
1. **Independent sources**: Each claim must have >= 2 unique domains among its source URLs
2. **Circular references**: No source URL may point to the evidence file itself; no two claims may share an identical domain set
3. **Monotonic timestamps**: All ISO/date timestamps in the file must be non-decreasing top-to-bottom

## Test results (ran this pass)
| File | Expected | Result | Details |
|------|----------|--------|--------|
| tests/evidence_good_A.md | PASS | PASS | 2 claims, both with 2 independent domains; timestamps monotonic |
| tests/evidence_good_B.md | PASS | PASS | 2 claims, both with 2 independent domains; timestamps monotonic |
| tests/evidence_good_C.md | PASS | PASS | 2 claims, both with 2 independent domains; timestamps monotonic |
| tests/evidence_bad_D.md | FAIL | FAIL | 3 issues: claim 1 has 1 domain, claim 2 has same-domain URLs, non-monotonic timestamp |

## Test fixtures location
- `memory/researcher/tests/evidence_good_A.md` — mirror revert + sandbox path claims
- `memory/researcher/tests/evidence_good_B.md` — KB search endpoint + migration claims
- `memory/researcher/tests/evidence_good_C.md` — stale checker behavior + queue output claims
- `memory/researcher/tests/evidence_bad_D.md` — deliberately corrupted (single-source, same-domain, time regression)

## Exit code contract
- 0 = all files pass
- 1 = one or more files fail (details printed to stdout)
- 2 = usage error / file not found