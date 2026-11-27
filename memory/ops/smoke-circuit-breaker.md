# Workflow: Smoke-Suite Remediation Circuit Breaker (Forge, 2026-11-27)
Round topic: Fleet Autonomy Convergence. Status: SHIPPED + self-tested (see evidence leaf).

## Why
An autonomous gate that "fixes" a host must not hammer a host that is structurally
unreachable. Unbounded retry = thrash + wasted WinRM/recover_all cost + log noise. A
circuit breaker gives the fleet autonomy WITH self-throttling: keep trying, but back off
on persistent failure and re-engage automatically.

## Pattern (reusable for any auto-remediation loop)
1. Track per-target consecutive-failure count + last-attempt ts in a small JSON state file.
2. Decision is PURE (should_remediate(name, state)) -> unit-testable with synthetic clocks.
3. OPEN after N consecutive failures; while open, SKIP the expensive action (log only).
4. Re-arm once per cooldown window (one retry); CLOSE immediately on first success.
5. Persist state across scheduler cycles so backoff survives process restarts.

## Applied to smoke_suite.py
- State: memory/forge/smoke_circuit.json  (host -> {consec_fails, last_remedy_ts})
- Knobs: CB_OPEN_AFTER=3, CB_COOLDOWN_S=900 (top of file).
- Self-test: python memory/forge/smoke_suite.py --self-test (8/8, no network).

## Division of labour (avoids duplication)
- Mechanic's fleet-status circuit breaker guards the PROBE API (read path).
- This one guards the REMEDIATION action (write path). Both are needed.

## If a host is genuinely down for hours
Expected: 3 failed attempts, then silent skips every 15 min with CIRCUIT OPEN log lines.
That is correct behaviour - not a bug. To force an immediate retry, delete the host's key
from smoke_circuit.json (or lower CB_COOLDOWN_S).
