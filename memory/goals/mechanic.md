# Mechanic - Cycle 17 Goals (set 2026-11-24)
Round topic: **Fleet Self-Optimization & Steady-State Convergence**
Pillars: (1) Predictive Operations, (2) Adaptive Resource Allocation, (3) Convergence Metrics

1. **Predictive Seat Health Monitor** - extend seat_probe.py: track response-time trend per seat; p95 latency up >50% over 3 probes = "degrading" state (before "down"). Write trend to seat-matrix.json. Verified: simulated latency ramp triggers degrading < actual failure.
2. **Steady-State Ops Playbook** - memory/mechanic/steady-state-playbook.md: reduced probe freq (15min), lighter recovery, escalate only on SLA breach. >=4 procedures with trigger+steps+rollback. Verified: all 4 have complete fields; referenced by fleet-mode.json in steady-state.
3. **Cycle Duration Ops Tracker** - measure wall-clock per cycle (first goal set -> last verified). Log to memory/ops/cycle-durations.jsonl. Rolling 3-cycle mean+stddev. Flag if current > mean+2*sigma. Verified: 5 entries logged; outlier correctly flagged.
4. **VRAM Headroom Predictor** - from VRAM usage history + load patterns, predict when host will run low. Alert before OOM (not after). Output: memory/ops/vram-forecast.json per-host. Verified: backtest 7 days; alerts fire >30min before low-VRAM event.
5. **Probe Cadence Auto-Adjuster** - STEADY-STATE mode: auto-reduce probes from 5min to 15min. On exit, restore. Log cadence changes. Verified: mode change triggers within 1 probe cycle; no missed detections (simulated).
6. **Recovery SLA Summary Data** - expose recovery-times.jsonl as structured JSON for panel: per-type mean, p95, trend, SLA compliance pct. Output: memory/ops/recovery-sla-summary.json. Verified: 3 incident types complete; compliance matches raw data.
7. **Convergence Infra Health Check** - weekly: verify seat-matrix fresh, autonomy-score updated, intervention log growing, cycle estimator running. Output: memory/ops/convergence-health.json (pass/fail per check). Verified: healthy=all PASS; simulated staleness detected.
8. **Decision Quality Tracker** - from auto-ops-decisions.jsonl: pct decisions with positive outcome (no follow-up <24h). Track trend. Alert if <80%. Output: memory/ops/decision-quality.json. Verified: 20 test decisions; quality correct; drop triggers alert.
9. **Transition Gap SLA** - measure time from goal_pct=100 to new cycle goals set. Target <4h. Log each transition. Flag if >4h. Output: memory/ops/transition-gaps.jsonl. Verified: 3 simulated transitions; gap>4h correctly flagged.
10. **Convergence Pipeline Load Test** - stress test: write 100 interventions in 1min, update autonomy score 50x in 1min. Verify no corruption, response <500ms. Output: memory/mechanic/convergence-loadtest.md. Verified: 0 corruption; p95<500ms; no deadlocks.
