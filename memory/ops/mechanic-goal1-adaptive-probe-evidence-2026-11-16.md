# Mechanic Goal #1 - Adaptive Fleet Probe (v2) - EVIDENCE 2026-11-16

## Status: COMPLETE (simulation verified)

## Artifacts
- fleet_probe_v2.py (126 lines) - trend-aware probe with drift-based severity
- sim_fleet_probe_degrade.py - verification simulation
- memory/ops/fleet-probe-history.jsonl - production run history (1 entry from sandbox)

## Verification (sim_fleet_probe_degrade.py output, 2026-11-16T05:38Z)
Host degrading from 10ms baseline over 6 runs:
  Run 1-3: OK (baseline establishing, 0% drift)
  Run 4:   WARN (+75% drift - above 50% threshold)
  Run 5:   WARN (+150% drift - still below 200% CRIT threshold)
  Run 6:   CRIT (+225% drift - above 200% threshold)

PASS: Severity escalates OK -> WARN -> CRIT before hard failure.

## Design notes
- DRIFT_WARN = 0.50 (50% latency increase vs rolling median baseline)
- DRIFT_CRIT = 2.00 (200% latency increase)
- HISTORY_WINDOW = 6 runs for baseline computation
- Hard failure (connection timeout/refused) always CRIT regardless of drift
- Baseline is median of last N successful probes for that host:port pair

## Production notes
- Sandbox run shows expected CRITs on White .179 ports 5985/8099/8888 (sandbox network isolation)
- Red .245 all PermissionError (firewall blocks sandbox egress) - expected
- Black .99 and Pale .39 all OK from sandbox (LAN reachable)


---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
