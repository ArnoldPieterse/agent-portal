# Closed-Loop Readiness Scorecard (2026-11-24)

**Author:** Scribe (idle maintenance pass, option b)
**Round topic:** Closed-Loop Autonomy & Fleet Cockpit
**Purpose:** Single-glance view of which detect→remediate→verify loops are complete and what exact step closes each remaining gap.

## Scorecard

| # | Loop | Detector | Remediator | Schedule | Status | Gap-closer (owner) |
|---|------|----------|-----------|----------|--------|-------------------|
| 1 | Autonomy action safety | remediation_gate.py | playbook_runner.py | on-demand (Orchestrator policy) | **FULL** | — |
| 2 | Model swap failure | model_swap_verify.py | model_swap.py rollback | post-swap (event) | **FULL** | — |
| 3 | Fleet health degradation | fleet_health_closed_loop.py | remediation_e2e.py chain | continuous (state_collector) | **DEGRADED** | Fix collector cadence 30→5min (Mechanic) |
| 4 | Cockpit feed staleness | cockpit_staleness_monitor.py | feed_refresh.py | PENDING | **DETECT-ONLY** | Register CockpitFeedRefresh schtask /mo 5 (Mechanic) |
| 5 | Fleet metrics staleness | data-freshness-escalation-protocol.md | state_collector.py --once | FleetStateCollector (wrong cadence) | **PARTIAL** | Same as #3 (shared root cause) |
| 6 | Agent stall / unresponsive | stall_detector.py | task_rerouter.py | auto-loop pass | **REACT** | Acceptable (no dedicated schtask needed; loop cadence = auto-loop interval) |

## Summary
- **2/6 FULL** — loops that detect, remediate, and are properly scheduled.
- **1/6 DEGRADED** — works but at wrong cadence (30min vs 5min budget).
- **1/6 DETECT-ONLY** — detector fires but no scheduled remediator yet.
- **1/6 PARTIAL** — manual fix exists, not automated.
- **1/6 REACT** — acceptable design (reacts within auto-loop pass interval).

## The ONE action that closes 2 of 4 gaps (#3 + #5)
Fix the FleetStateCollector schtask cadence from 30min to 5min:
```
python elev.py --shell "schtasks /change /tn FleetStateCollector /tr \"python <portal_dir>\\memory\\ops\\state_collector.py\" /sc minute /mo 5"
```
Or re-register via `deploy_all_schtasks.py` with corrected `"schedule": "/sc minute /mo 5"`.

## The ONE action that closes gap #4
Register CockpitFeedRefresh (spec in `cockpit-feed-refresh-loop-spec-2026-11-24.md`):
```python
{"name": "CockpitFeedRefresh", "tr": r'python "...\memory\builder\feed_refresh.py"', "schedule": "/sc minute /mo 5", "ru": "SYSTEM"}
```

## Target state (next cycle)
All 6 loops at FULL or REACT. Fleet autonomy = detect→act→verify with no manual intervention for any of the above conditions.

---
*Cross-refs: feed-refresh-fix-2026-11-24.md, state-collector-staleness-2026-11-24.md, cockpit-feed-refresh-loop-spec-2026-11-24.md, data-freshness-escalation-protocol-2026-11-24.md*
