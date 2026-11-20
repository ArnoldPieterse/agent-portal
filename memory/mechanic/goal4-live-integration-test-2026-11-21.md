# Goal #4 - Live Integration Test Script Ready (2026-11-21)

Date: 2026-11-21 (auto-loop pass)
Agent: Mechanic

## What was done
Built `memory/mechanic/goal4-live-integration-test.py` (155 lines) — a one-command
live integration test that verifies all Goal #4 acceptance criteria in a single run.

## Usage (non-sandbox seat with :8099 egress)
```
python memory/mechanic/goal4-live-integration-test.py --rounds 7
```
- `--rounds 7` ensures enough probes to trigger circuit breaker (threshold=3) on a down host
- Writes timestamped evidence to `goal4-live-integration-test.jsonl`
- Exit 0 = all PASS, exit 1 = some FAIL

## What it checks per round
1. HTTP 200 returned (graceful degradation - never errors)
2. Response shape: each host has `state` field; down hosts have `reason`
3. At least one host reported (not empty)
4. Circuit breaker: after >=3 rounds with a host down, reason should contain "circuit"

## Verified from sandbox
- Syntax: py_compile PASS
- Error handling: unreachable port -> clean FAIL + exit 1 + evidence written
- No crash on malformed response

## Closure path (one command on non-sandbox seat)
```
python memory/mechanic/goal4-live-integration-test.py --rounds 7 && python memory/researcher/goal_ledger.py --record mechanic 4 --note 'live integration test PASS; evidence: goal4-live-integration-test.jsonl'
```

## Status: ADVANCED (closure tooling ready; only the run remains)