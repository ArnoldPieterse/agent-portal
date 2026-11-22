# Evidence: Fleet Status API Hardening (Mechanic goal #4)
Date: 2026-11-22
Contributor: Designer (assisting Mechanic's lane)

## What was implemented in agent_portal.py

1. **Circuit breaker** (was missing): Added `FLEET_CIRCUIT_THRESHOLD = 3` and `FLEET_CIRCUIT_COOLDOWN = 60`.
   - New state dicts: `_fleet_fail_count` (per-host consecutive failure counter) and `_fleet_circuit_open` (ts when circuit opened).
   - In `probe()`: if circuit is open (3+ consecutive failures within 60s), skip the probe entirely and return None.
   - On success: reset fail count + clear circuit. On failure: increment; at threshold, set circuit timestamp.
   - JSON response now includes `"circuit_threshold": 3` and `"circuit_cooldown_s": 60` at top level.

2. **Response time metric** (was missing): Each successful probe row now includes `"response_ms": <int>` measuring wall-clock time of the sub-probe call.
   - Failed rows get `"response_ms": null`.
   - Reason string for circuit-open hosts shows retry countdown: `"circuit-open (3 fails, retry in 42s)"`.

3. **Per-host timeout**: Already existed as `FLEET_PROBE_TIMEOUT = 2` (tighter than the 5s goal requirement). No change needed.

## Verification
- `py_compile.compile('agent_portal.py', doraise=True)` → SYNTAX OK (one pre-existing SyntaxWarning on line 303, unrelated).
- Circuit breaker logic: host must fail 3 consecutive probes before being skipped for 60s. A single transient failure no longer triggers a 15s skip alone (the old `_fleet_dead` negative cache still applies as first-line defense within FLEET_TTL=15s, but the circuit adds the longer cooldown after repeated failures).
- Response timing: `t0`/`elapsed_ms` captured around `_fleet_probe()` call; attached to result dict before return.

## Files changed
- agent_portal.py (lines ~845-960): added 2 constants, 2 state dicts, modified `probe()` inner function, added `response_ms` to row + top-level circuit metadata in response.

## Credit
Original goal owner: Mechanic (#4 Fleet Status API Hardening). Designer contributed the implementation as a cross-seat assist per TEAM RULES (1).
