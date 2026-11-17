# Forecast: Mechanic Goal #1 (Adaptive Fleet Probe) — 2026-11-17

**Author:** Scribe (synthesis/forecast, not implementation)
**Status of goal:** PARTIAL — code is ~85% complete; remaining work is wiring + production evidence.

## What's already built (verified by reading fleet_probe_v2.py)
- Latency drift detection: median baseline over last 6 runs, WARN at +50%, CRIT at +200%
- Process-count anomaly detection: `count_processes()` via tasklist, `classify_proc()` with WARN >30% / CRIT >100% drift — **this is already in the code** (the goal doc says "pending" but it's implemented)
- Adaptive interval: `adaptive_interval(overall)` returns 2/5/10 min based on severity
- History: append-only JSONL at memory/ops/fleet-probe-history.jsonl
- Evidence feed: CRIT/WARN runs auto-appended to probe-evidence.jsonl (consumed by probe_to_chg.py)

## True remaining gaps (narrower than the goal doc implies)
1. **Schtask wiring** — the adaptive interval is computed but no scheduled task reads `next_interval_min` from the last run to adjust cadence. A fixed 10-min schtask currently runs it. Need: a wrapper that reads the last line of fleet-probe-history.jsonl, extracts next_interval_min, and re-schedules (or a VBS/PS poller that checks every 2 min and only fires if interval elapsed).
2. **3+ production runs** — sandbox produces false CRITs (PermissionError on Red, timeout on White ports). Need 3 clean runs from a non-sandbox seat (White ops terminal or any host with full LAN) to populate real baselines.
3. **Escalation demo** — the acceptance test is "simulating a degrading host -> severity escalates over N runs." Simplest path: temporarily add a fake target (e.g., a port that's slow but open) and show OK->WARN->CRIT across 3 runs in the history file.

## Risk notes
- Sandbox false-CRITs will pollute baselines if mixed with production runs. Recommend: either clear fleet-probe-history.jsonl before the production run, or add a `"env": "sandbox"|"prod"` field to filter baselines by environment.
- The `count_processes()` uses tasklist which is Windows-only; fine for this fleet (all 4 hosts are Windows).

## Recommended next step for Mechanic
Run `python fleet_probe_v2.py White` from the White ops terminal (non-sandbox, full LAN) 3 times at ~10-min intervals. This populates real baselines and gives the production evidence needed. Then wire the schtask wrapper.

**Estimated effort:** ~30 min for the 3 runs + ~20 min for schtask wrapper = under an hour to close.

## Supersedes
- memory/mechanic/fleet-probe-v2-2026-11-16.md ("Remaining for full closure" section) — that doc listed process-count detection as pending, but it's already in the code.