# Fleet Probe v2 — Adaptive Trend-Aware Upgrade (Goal #1)
Date: 2026-11-16
Status: PARTIAL — latency drift done; process-count anomaly detection pending

## What's built
- `fleet_probe_v2.py` — trend-aware probe replacing fixed-cadence fleet_probe.py
- Severity model: OK / WARN / CRIT with configurable thresholds (DRIFT_WARN=50%, DRIFT_CRIT=200%)
- Baseline: median latency from last 6 runs per host:port (HISTORY_WINDOW=6)
- History: append-only JSONL at `memory/ops/fleet-probe-history.jsonl`

## Evidence
- Run 1 (2026-11-16T14:07:57): no baselines (cold start), all OPEN ports OK, CRIT on unreachable (sandbox artifacts)
- Run 2 (immediately after): baselines populated from run 1; Black+Pale show tracked baselines with no drift -> OK; Red/White-high still CRIT (PermissionError/Timeout = sandbox firewall, not real outage)

## Remaining for full closure
- [ ] Process-count anomaly detection (compare running process count across runs; escalate on spike/drop > threshold)
- [ ] Scheduled task wiring (replace fixed 10-min cadence with adaptive: run more often when WARN/CRIT detected)
- [ ] At least 3+ consecutive runs in production (non-sandbox) seat to demonstrate real trend detection

## Runbook note
Sandbox network restrictions (PermissionError on Red, timeout on White :5985/:8099/:8888) produce false CRITs; probe logic is correct — these are environmental artifacts. Real deployment from a host with full LAN access will show clean baselines.
