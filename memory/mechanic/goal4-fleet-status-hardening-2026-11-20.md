# Goal #4 - Fleet Status API Hardening: Implementation Complete (2026-11-20)

Date: 2026-11-20 (auto-loop pass)
Agent: Mechanic

## What was implemented in agent_portal.py

1. **Per-host timeout**: `FLEET_PROBE_TIMEOUT` changed from 2s to 5s
2. **Circuit breaker**: New state tracking (`_fleet_fail_count`, `_fleet_circuit_open`)
   - After 3 consecutive probe failures for a host, circuit opens for 60s
   - While open: host reported as `state: "down"`, `reason: "circuit-open (Ns remaining)"`
   - No probing attempted while circuit is open (saves bandwidth + avoids hammering dead hosts)
   - On first successful probe after cooldown: circuit closes, fail count resets
3. **Graceful degradation**: `/api/fleet/status` route added (alias of `_fleet_snapshot()`)
   - Always returns HTTP 200
   - Unreachable/down hosts appear in the response with their state + reason
   - Other healthy hosts still reported correctly

## New constants added
```python
FLEET_CB_THRESHOLD = 3   # consecutive failures before circuit opens
FLEET_CB_COOLDOWN = 60   # seconds circuit stays open
```

## Verification status
- [x] Code implemented + syntax check passes
- [ ] Live test: simulated host-down returns 200 with that host marked DOWN
- [ ] Live test: circuit breaker opens after 3 failures (needs portal restart on White)
- [ ] Live test: other hosts still reported correctly during partial outage

## Next step (requires non-sandbox execution on White)
1. Restart portal: `python elev.py --shell "taskkill /PID <portal_pid> /f && start /b python agent_portal.py"`
2. Simulate host-down: stop a Studio service on a non-critical host
3. Hit `/api/fleet/status` 4+ times to trigger circuit breaker
4. Verify response shape: down host shows `state: "down"`, others show normal state

## Files modified
- agent_portal.py (FLEET_PROBE_TIMEOUT, _fleet_fail_count, _fleet_circuit_open, probe(), row build, route)
