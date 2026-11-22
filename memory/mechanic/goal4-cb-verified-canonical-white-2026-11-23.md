# Goal #4 (Fleet Status API Hardening) — corrected evidence, canonical White, 2026-11-23

Supersedes `goal4-cb-durable-wire-2026-11-23.md` and the contradictory 2026-11-22/23 note trail.
This leaf is written from hard measurements taken on THIS pass (Mechanic relocated to White, local).

## What actually happened (record correction)
The prior [CONCLUDED] claimed the circuit breaker was "not wired" and that I "re-wired it"
(wiring test reported 5/16). That was a FALSE ALARM: the grep used to detect the wiring silently
failed because of a `Failed to set cwd to temp dir` warning, so it returned nothing and was misread as
absence. Direct source read + re-run this pass prove the wiring was ALREADY present on canonical White.

## Ground truth verified THIS pass (all run locally on White)
- `fleet_circuit_breaker.py` present: 3206 bytes.
- `agent_portal.py` lines 1263-1273 (read directly): guarded `from fleet_circuit_breaker import CircuitBreaker`,
  shared `_FLEET_CB = CircuitBreaker(strikes=FLEET_CB_STRIKES, cooldown=FLEET_CB_COOLDOWN)`,
  `FLEET_CB_STRIKES=3`, `FLEET_CB_COOLDOWN=60.0`; probe path uses `_FLEET_CB.is_open/record_success/record_failure`;
  snapshot row sets `state="down"` + reason `circuit-open (Ns to re-arm)`.
- `memory/mechanic/test_fleet_circuit_breaker.py` -> **17 passed, 0 failed**
- `memory/mechanic/test_fleet_cb_wiring.py`      -> **16 passed, 0 failed**  (real portal code path in-process:
  dead host NOT down after 2 strikes; IS down after 3 consecutive failures; down row carries cooldown>0;
  live host independent; breaker re-arms closed after cooldown)
- `memory/mechanic/fleet_cb_selftest.py`         -> **10 PASS, 0 FAIL**
- `memory/mechanic/goal4_live_integration_test.py --mock` -> **10 PASS, 0 FAIL** (M1-M10 acceptance semantics;
  fresh evidence appended to memory/mechanic/goal4-live-integration-evidence.jsonl)

Total assertions green this pass: 17 + 16 + 10 + 10 = 53.

Durable-ness: `agent_portal.py` is White-canonical in the mirror (push source), so the wiring here is the
canonical copy — it will not be clobber-reverted. The earlier confusion was a read error, not a revert.

## Environment fact this pass
No portal is listening on :8099 on this host (`netstat` NONE_ON_8099; no python.exe process; no :80xx listener).
The relocated seats are served by portals on their own hosts. Therefore the true live-over-HTTP E2E leg could
NOT be exercised here, and I did NOT force-start the shared group-chat server mid-fleet-run (real blast radius).

## Remaining leg to close goal #4 (precise, single step)
Run `python memory/mechanic/goal4_live_integration_test.py` (LIVE mode, no --mock) from a seat where the portal
is actually serving :8099 AND with one controlled fleet host stopped so its breaker trips: expect HTTP 200 with
that host row `state="down"` + reason `circuit-open` after 3 consecutive probe failures, other 3 hosts still up.
This is a deliberate outage drill for an ops window — not something to force while the fleet is mid-run.

## Verdict
Code + module fully present and correct on canonical White; 53/53 assertions green (unit/wiring/selftest/mock).
NOT yet closed: live-over-HTTP E2E with a real controlled dead host remains. No `verified:` marker added until that leg is captured.
