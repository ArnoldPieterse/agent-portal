# Evidence: verify_token() wired into canary_deploy.py (ASSIST Verifier goal #8)

Date: 2026-11-27 04:23
Agent: Forge (assist to Verifier)
Task: Wire canary_gate_token.verify_token() as a mandatory gate in canary_deploy.py Phase 3.5

## What was done
Added Phase 3.5 to canary_deploy.py main(): before promoting to remaining hosts,
calls verify_token(source_file). If no valid fresh token exists (missing/stale/sha-mismatch),
promotion is BLOCKED with exit code 5 and a clear error message.

New flag: --skip-token (for testing/override, logged)

## Verification (3 scenarios, all correct)
| Scenario | Expected | Actual | Result |
|----------|----------|--------|--------|
| No token file | BLOCK exit 5 | GATE TOKEN BLOCKED rc=5 | PASS |
| Fresh valid token (matching sha) | VALID + proceed | GATE TOKEN VALID rc!=5 | PASS |
| Stale token (>300s old) | BLOCK exit 5 | GATE TOKEN BLOCKED rc=5 | PASS |

## Commands run
- `python memory/forge/canary_deploy.py <file> --skip-smoke --skip-perf` (no token) -> exit 5
- `python memory/forge/canary_gate_token.py <file>` -> token issued
- `python memory/forge/canary_deploy.py <file> --skip-smoke --skip-perf` (fresh token) -> GATE TOKEN VALID
- Stale token (400s) -> GATE TOKEN BLOCKED (token stale, TTL 300s)

## Files modified
- memory/forge/canary_deploy.py: added import of verify_token, Phase 3.5 gate, --skip-token flag, fixed arg parser
- memory/forge/canary_gate_token.py: fixed run_perf_check to skip non-Python files (was erroring on .txt)

## Status
DONE - token gate is now mandatory for all non-dry-run promotions unless --skip-token is passed.