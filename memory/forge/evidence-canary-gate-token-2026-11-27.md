# Evidence: Canary Gate Token Mechanism (ASSIST - Verifier goal #5)

**Date:** 2026-11-27
**Agent:** Forge (assisting Verifier)
**Goal served:** Verifier #5 - Canary gate verification

## What was built
`memory/forge/canary_gate_token.py` - pass/fail token mechanism for canary promotions.

## How it works
1. `python memory/forge/canary_gate_token.py <target_file>` runs smoke + perf checks, emits JSON token to `memory/ops/canary-gate-token.json`
2. `python memory/forge/canary_gate_token.py --verify [target]` checks token freshness (300s TTL) + sha match
3. canary_deploy.py can import `verify_token()` to gate promotions

## Verification (3 scenarios, all pass)
| # | Scenario | Command | Result |
|---|----------|---------|--------|
| 1 | Token present + fresh | --verify after issue | VALID: age 0s, signer=forge |
| 2 | Token missing | deleted token, then --verify | INVALID: no token file found |
| 3 | Token stale (600s > 300s TTL) | backdated ts, then --verify | INVALID: token stale (600s old, TTL 300s) |

## Perf evidence
- Parse check p50: 1.28ms (limit 2000ms) - PASS
- Token issuance + verification round-trip: <1s

## Files created/modified
- memory/forge/canary_gate_token.py (new, 174 lines)
- memory/ops/canary-gate-token.json (emitted at runtime)

## Integration note
canary_deploy.py currently has no token check yet. Next step: add a `verify_token()` call
before the promotion loop in canary_deploy.py (line ~250 area, after dispatch gate).
