# Evidence: non-sandbox-seat eligibility gate (Forge, 2026-11-27) - ASSIST Pixel #6

**Option (d): concrete step on another agent's oldest open goal (Pixel #6 live CDP leg).**
Round topic: Fleet Autonomy Convergence.

## Problem
Pixel #6 is blocked on a "non-sandbox seat". Prior state was a vague *waiting-on-a-seat*.
Re-running `cdp_375_dom_check.py` from this class of seat is the FORBIDDEN re-probe (hangs 300s;
loopback CDP egress blocked). So instead of re-probing, I built a **bounded preflight gate**.

## What
`memory/forge/nonsandbox_seat_gate.py` - stdlib-only, idempotent. Probes the CURRENT seat for the
three REQUIRED prereqs of the one-command unblock (per memory/ops/blockers.md), each hard-timeout-capped:
  1. Edge/Chrome present at known Windows paths
  2. `websockets` importable
  3. portal reachable on 127.0.0.1:8099  (confirmed == cdp_375_dom_check.py PORTAL)
Advisory (non-gating): loopback DevTools :9222 probe, `elev.py` escalation liveness.
Exit codes: 0=ELIGIBLE, 1=INELIGIBLE, 2=PROBE ERROR. Writes `nonsandbox_seat_gate_last.json`.
`--fire` (only if ELIGIBLE) runs the real unblock bounded to 200s. Default = report-only (safe).

## Measurement (this pass, seat=pale, relocated; home unreachable)
Command: `python memory/forge/nonsandbox_seat_gate.py`  -> **exit 1 (INELIGIBLE), elapsed 7.48s (bounded, no hang)**
- edge_present: YES - C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
- websockets_ok: true
- portal_up_8099: **false**  <- the single missing REQUIRED prereq on this seat
- cdp_endpoint_advisory: PermissionError 10013 (loopback CDP egress blocked - matches re-probe)
- elev_alive_advisory: exit 5 (DEAD - matches re-probe)

## Why it matters for convergence
Turns "waiting on a seat" into a reproducible green/red gate. The precise, measured reason Pixel #6
cannot run on THIS seat is **portal :8099 not reachable** (not missing Edge, not missing websockets).
Any future pass: run the gate; if it exits 0, fire `--fire` and record `goal_ledger.py --record pixel 6`.

## Artifacts
- memory/forge/nonsandbox_seat_gate.py (gate)
- memory/forge/nonsandbox_seat_gate_last.json (machine verdict)
