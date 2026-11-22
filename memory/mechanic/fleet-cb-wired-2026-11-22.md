# Goal #4 - Circuit Breaker NOW WIRED into live _fleet_snapshot (2026-11-22)

## What was wrong (drift / hollow claim)
The prior goal note said the 3-strike/60s breaker was "BUILT in fleet_circuit_breaker.py + wired into
_fleet_snapshot() with explicit state=down; unit test 17/17 PASS". Re-auditing the ACTUAL file on
2026-11-22 showed that is FALSE against the shipped code:
- `fleet_circuit_breaker.py` (root, CircuitBreaker class) + `test_fleet_circuit_breaker.py` existed and passed 17/17.
- But `agent_portal.py` had ZERO breaker markers: no import, no `_FLEET_CB`, no fail counter, no
  `state="down"`. The live /api/fleet only had the single-shot 15s negative cache (FLEET_TTL).
The module was built but never wired in (or a mirror LWW cycle reverted the wiring). Net effect:
the circuit-breaker sub-feature of goal #4 was NOT active on the live endpoint.

## What I did this pass (sandbox-safe, reversible, no network/elevation)
1. Wired the existing breaker into `_fleet_snapshot()` in agent_portal.py (3 minimal edits):
   - Guarded import + shared instance: `FLEET_CB_STRIKES=3`, `FLEET_CB_COOLDOWN=60.0`,
     `_FLEET_CB = _FleetCB(...)` with a no-op fallback so a missing module can't crash the portal.
   - `probe(b)`: skip probing while `_FLEET_CB.is_open(b)`; feed the breaker (success->record_success,
     failure->record_failure). Negative cache means strikes accumulate ~once per FLEET_TTL window,
     so 3 strikes ~= a sustained outage.
   - Row-building: when res is None AND circuit open -> `state="down"`, reason
     `circuit-open (Ns remaining)`; otherwise the prior unreachable/stale path is unchanged.
2. Added `memory/mechanic/test_fleet_cb_wiring.py` - a WIRING REGRESSION GUARD that FAILS if the
   wiring ever gets reverted out of agent_portal.py again: asserts the portal imports + instantiates
   the breaker, consults it in probe(), emits state="down"/circuit-open, and that FLEET_CB_STRIKES/
   COOLDOWN match the module defaults; plus a real-CircuitBreaker replay of the exact wiring sequence.

## Evidence (all ran this pass, from sandbox seat)
- `python -m py_compile agent_portal.py` -> COMPILE OK (pre-existing line-709 SyntaxWarning is an
  unrelated docstring path, present before this change).
- `python memory/mechanic/test_fleet_circuit_breaker.py` -> 17 passed, 0 failed (real module).
- `python memory/mechanic/test_fleet_cb_wiring.py` -> 16 passed, 0 failed (wiring guard + row rule).

## State / what remains
- Code + unit coverage for all three sub-features now present AND wired: per-host timeout
  (FLEET_PROBE_TIMEOUT=2s parallel -> full snapshot <5s), circuit breaker (3-strike/60s, state=down),
  graceful degradation (partial data, HTTP 200, other hosts still reported).
- STILL PENDING (non-sandbox only, do NOT re-probe from sandbox): the LIVE leg - a real /api/fleet
  returning HTTP 200 with an actually-down host marked state="down". Needs :8099 egress (WinError
  10013 wall here). One unblock on a non-sandbox White seat: hit /api/fleet with one remote down and
  confirm that host's row shows state=down + others report normally, then `--record mechanic 4`.
- Runbook note: CB was built-but-unwired (likely mirror revert); fixed by re-wiring in _fleet_snapshot
  + adding test_fleet_cb_wiring.py as the regression guard so a future revert is caught by CI/selftest.