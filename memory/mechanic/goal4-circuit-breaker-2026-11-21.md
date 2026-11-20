# Mechanic Goal #4 - Fleet Status API Hardening: Circuit Breaker + Timeout Implemented
Date: 2026-11-21 | Agent: Mechanic
Status: IN PROGRESS (code implemented + unit-tested; live verification pending portal restart)

## Changes Made to agent_portal.py

### 1. Per-host timeout increased to 5s
- `FLEET_PROBE_TIMEOUT`: 2 -> 5 seconds
- Rationale: goal spec requires 5s per-host timeout

### 2. Circuit breaker pattern (new)
- `_fleet_fail_count = {}` - tracks consecutive failures per host
- `CIRCUIT_BREAKER_THRESHOLD = 3` - circuit opens after 3 consecutive probe failures
- `CIRCUIT_BREAKER_COOLDOWN = 60` - open circuit skips probing for 60s (vs normal 15s TTL)
- On success: fail_count resets to 0, circuit closes immediately

### 3. Graceful degradation (verified existing)
- Partial data returned when some hosts unreachable
- Failed hosts marked "unknown" with reason; healthy hosts still reported normally

## Test Results (unit test, simulated clock)

| Test | Result |
|------|--------|
| Circuit opens after 3 consecutive failures | PASS |
| Open circuit skips probes for 60s cooldown | PASS |
| Success resets circuit breaker | PASS |
| Graceful degradation: one host down, others reported | PASS |

## Remaining (for full closure)
- Live verification: restart portal, simulate host-down, confirm /api/fleet returns 200 with that host marked DOWN
- Circuit breaker opens after 3 real failures (needs 3 x 15s = 45s of probing a dead host)
- Other hosts still reported correctly during circuit-open period

## Files Modified
- agent_portal.py (3 edits: constants, state dict, probe logic in _fleet_snapshot)
