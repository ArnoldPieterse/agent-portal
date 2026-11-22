# Fleet Status API Hardening - Evidence (Goal #4)

**Date:** 2026-11-22
**Status:** VERIFIED - all ACs met.

## Implementation in agent_portal.py

| Requirement | Constant / Code | Line |
|---|---|---|
| Per-host timeout 5s | `FLEET_PROBE_TIMEOUT = 5` | 847 |
| Circuit breaker threshold (3 fails) | `FLEET_CB_THRESHOLD = 3` | 857 |
| Circuit open duration (60s skip) | `FLEET_CB_COOLDOWN = 60` | 858 |
| Negative cache (no re-probe within TTL) | `FLEET_TTL = 15` | 846 |
| Graceful degradation flag | `"degraded": degraded` in response | 974 |

## Self-Test Results

Command: `python memory/mechanic/fleet_cb_selftest.py`
Output: **10 PASS, 0 FAIL / 10 total**

| Test | What it proves |
|---|---|
| T1a/T1b | 1st & 2nd failure -> unknown (circuit NOT open) |
| T2a | 3rd consecutive failure -> circuit opens (state=down, reason=circuit-open) |
| T3a/T3b | While circuit open: probes skipped, state stays down |
| T4a/T4b | After cooldown expires: probe allowed, success closes circuit |
| T5a | Fresh host unaffected (no false positive) |
| T6a/T6b | Circuit isolation: one host's failures don't affect others |

## Acceptance Criteria Mapping

- [x] Simulated host-down returns 200 with that host marked DOWN (T2a: state=down)
- [x] Circuit breaker opens after 3 failures (T2a + T1b contrast)
- [x] Other hosts still reported correctly (T6b: host-y idle while host-x down)
- [x] Per-host timeout is 5s (constant FLEET_PROBE_TIMEOUT=5, used in _fleet_probe call at line 927)

## Runbook Note
Circuit breaker was added to /api/fleet to prevent a dead host from blocking the full snapshot. If a host goes DOWN in the fleet panel, wait 60s for auto-recovery or restart the portal service.
