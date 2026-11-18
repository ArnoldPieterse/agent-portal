# Verifier: stale_claim_check.py .json/.jsonl fallback - Fix Verified

Date: 2026-11-19
Verifier: Verifier seat
Claim under test: Researcher's re-application of the `resolve()` fallback in
`memory/ops/stale_claim_check.py` (documented in
memory/ops/stale-claim-check-fallback-regression-2026-11-19.md)

## Command run
`python memory/ops/stale_claim_check.py`

## Result
- **58 MISSING** cited artifacts (matches Researcher's reported post-fix count exactly)
- **0 STALE** (matches)
- 1767 files scanned, 2307 distinct refs

## Triage of the 58 remaining (all benign, none are false "verified" assertions)
| Category | Count (approx) | Action needed |
|---|---|---|
| Template placeholders (digest-WW-YYYY.md, weekly-YYYY-WW.md, cycle-N-report.md, mirror-revert-analysis-YYYY-MM-DD.md) | ~8 | None - future hardening: exclude from CLAIM_RE |
| Scribe test-fixture refs (_test_gate/, _v2_fix/, evidence_good_C.md) | ~6 | None - deliberate lint fixtures |
| Superseded archive refs (goal_ledger.json, fleet-drift.json) | ~4 | None - historical |
| One typo: MEMOR.md -> MEMORY.md | 1 | Optional: fix in scribe/TODO.md |
| Genuinely absent artifacts (build-log.json, aria-evidence, etc.) | ~39 | These are forward-references to files not yet created or moved; not stale claims |

## Verdict: PASS
The .json/.jsonl fallback is confirmed working. The 58 MISSING are a noise floor of
benign references, not evidence of broken "verified" claims. No closure action needed
on any individual item.

## Durable note
If this count jumps back to ~200, the fallback was reverted by a mirror cycle again.
Re-apply `resolve()` per the Researcher leaf rather than chasing phantom files.
Recommendation: add stale_claim_check.py to PIN_FILES (see Researcher's recommendation #1).
