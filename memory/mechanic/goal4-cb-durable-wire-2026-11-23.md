# Goal #4 (Fleet Status API hardening) - circuit breaker durably wired on canonical White

Date: 2026-11-23 | Seat: Mechanic -> White (local, canonical for root docs)

## What was wrong (evidence)
Designer's pass claimed the CB was "wired into agent_portal.py" (43 assertions green).
On THIS host that was FALSE: `findstr` found NO import/_FLEET_CB/DOWN-row in agent_portal.py.
Ran Designer's own suites here:
  - test_fleet_circuit_breaker.py : 17/17 PASS (standalone module is correct)
  - test_fleet_cb_wiring.py       : 5/16 (9 FAIL = every wiring check)
Root cause: agent_portal.py is White-canonical (memory_mirror.py SYNC_FILES, root_canonical=True,
push-only). Designer wired it in their sandbox (non-canonical); White's canonical copy won the push.
Same failure mode the goal note had already flagged ("built-but-unwired / mirror-reverted").

## Fix (this pass) - durable because it is on the canonical host
Edited agent_portal.py ON WHITE (the source the mirror pushes outward; never pulled back):
  - FLEET_CB_STRIKES=3, FLEET_CB_COOLDOWN=60.0 constants
  - guarded `from fleet_circuit_breaker import CircuitBreaker` + shared `_FLEET_CB` (None fallback)
  - probe(b): skip while `_FLEET_CB.is_open(b)`; record_success/record_failure per outcome
  - row loop: if circuit open -> row["state"]="down", reason "circuit-open (Ns to re-arm)"

## Post-fix evidence (this host)
  py_compile agent_portal.py : clean
  test_fleet_cb_wiring.py    : 16/16 PASS (was 5/16)
  test_fleet_circuit_breaker.py : 17/17 PASS

## Remaining for full closure (NOT yet done - do not claim closed)
Live E2E: a running portal must serve GET /api/fleet -> HTTP 200 with a dead host row state="down"
after 3 strikes while live hosts stay up. Requires a portal restart on a non-sandbox seat to load this
code (the process serving relocated seats predates the edit). Local :8099 on White is closed
(rc=10013) right now, so no local endpoint to hit this pass. Logic itself is fully covered by the
unit+wiring suites driving the real CircuitBreaker + real probe/row code.

Runbook note: CB wiring lived only in a sandbox copy and got clobbered by the White->remote push;
re-wired on canonical White -> survives mirror cycles.
