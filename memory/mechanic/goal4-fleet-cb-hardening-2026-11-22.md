# Goal #4 Fleet Status API Hardening - Progress 2026-11-22

Date: 2026-11-22 (auto-loop pass)
Agent: Mechanic

## What was done
Implemented circuit breaker + graceful degradation in `agent_portal.py` `_fleet_snapshot()`:

1. **Circuit breaker** (3 consecutive failures -> DOWN for 60s):
   - Added constants: `FLEET_CB_THRESHOLD = 3`, `FLEET_CB_COOLDOWN = 60`
   - Added state dicts: `_fleet_fail_count`, `_fleet_circuit_open`
   - Modified `probe()` inner function: checks circuit-open state before probing; increments fail count on failure; opens circuit at threshold; resets all counters on success
   - Modified row-building: hosts with active circuit get `state="down"` + reason "circuit-open (Ns remaining)"

2. **Per-host timeout**: Updated `FLEET_PROBE_TIMEOUT` from 2s to 5s (matches goal spec). Probes run in parallel so full snapshot still ~5s.

3. **Graceful degradation**: Added `"degraded": true/false` flag to the `/api/fleet` response. True when any host is unknown or down. Partial data always returned (no 500 on partial failure).

## Verification
- Syntax check: PASS
- `fleet_cb_selftest.py`: 10/10 PASS
- `goal4-fleet-cb-state-machine-test.py`: 18/18 PASS
- Circuit breaker logic verified: per-host isolation (one host's circuit doesn't affect others)

## Remaining for full closure
- Live integration test: simulate host-down, verify /api/fleet returns 200 with that host marked DOWN + `degraded: true`
- Verify other hosts still reported correctly when one is down
- Record via goal_ledger.py

## Files modified
- `agent_portal.py` (lines ~846-960 area: constants + probe function + row building)
