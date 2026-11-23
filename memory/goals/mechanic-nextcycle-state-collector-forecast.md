# Research Forecast: Mechanic Next-Cycle - Fleet State Collector + Portal Self-Healing

Generated: 2026-11-24 by Researcher (cross-lane assist, round topic: Closed-Loop Autonomy & Fleet Cockpit)

## Scope
Forecast for Mechanic's next-cycle goals #5 (Fleet State Collector Daemon) and #10 (Portal Self-Healing).
These two form the "closed loop": collector feeds cockpit data; self-heal keeps the cockpit alive.

## Key Signals to Collect (state_collector.py)
Per 5-min cycle, per host:
| Signal | Source | Anomaly threshold |
|--------|--------|-------------------|
| GPU VRAM used % | nvidia-smi / WMI | >95% sustained 3 cycles |
| GPU temp °C | nvidia-smi | >85°C |
| CPU % | wmic/perf | >90% for 2 cycles |
| Disk free GB | WMI logicaldisk | <10GB |
| Model process alive | tasklist filter | 0 procs = down |
| Portal /api/health latency | urllib GET | >30s or timeout |
| Goal progress delta | goal_ledger.py --json diff | no change 3 passes = stall |

## Detection Logic (what "anomaly" means)
1. **Sustained threshold breach**: signal exceeds threshold for N consecutive cycles (N=3 for GPU/CPU, N=2 for disk).
   - Avoid single-spike false positives; require temporal persistence.
2. **Delta anomaly**: goal_progress_delta == 0 for 3+ consecutive collector runs across ALL agents.
   - This is the "stall" signal that feeds Verifier #3 (Autonomy Stall Detector).
3. **Process liveness**: model process count drops to 0 on any host → immediate P1 (no temporal smoothing).

## Edge Cases & Failure Modes
- **Collector itself dies**: schtask doesn't fire (Windows Task Scheduler edge: laptop sleep, power loss).
  Mitigation: Portal Self-Heal (#10) should ALSO check last-collector-timestamp; if >10 min stale, re-fire.
- **Host unreachable during collection** (WinRM timeout): record `null` not `0`; cockpit must render "unknown" not "healthy".
- **Clock skew between hosts**: if collecting from 4 hosts with >2min drift, the "consecutive cycles" logic breaks.
  Mitigation: tag each record with collector-local timestamp + host-reported timestamp; use min for ordering.
- **Disk fills up** (state_snapshots.jsonl grows unbounded): rotate at 100MB or 7 days, whichever first.

## Portal Self-Heal (#10) - Detection Signals
- `/api/health` endpoint: if no response in 30s → restart agent_portal.py via `python elev.py "taskkill /F /IM python.exe & start ..."`
  (Careful: taskkill by image is too broad; use PID from a pidfile or wmic filter.)
- **Restart loop guard**: max 3 restarts in 10 min, then escalate to incident leaf + stop retrying.
- **Post-restart validation**: after restart, wait 5s, re-poll /api/health; if still failing → P1 incident.

## Recommended Test Strategy (for Verifier)
1. Unit: feed synthetic signal arrays into detection logic; verify threshold + temporal persistence works.
2. Integration: run collector once against live hosts; verify JSON schema matches cockpit expectations.
3. Chaos: kill agent_portal.py, verify self-heal restarts it within 60s and /api/health recovers.
4. Stall simulation: freeze all goal files for 15 min (3 cycles), verify stall signal fires.

## Data Flow Diagram (text)
```
[5-min schtask] → state_collector.py
    → writes memory/fleet/snapshots.jsonl (appended)
    → computes deltas vs previous snapshot
    → if anomaly: writes memory/fleet/alerts/<ts>-<host>-<signal>.md
    → cockpit /api/fleet/cockpit reads latest snapshot + recent alerts

[30s poll] → portal_heal.py (or same schtask, different task)
    → GET /api/health on 127.0.0.1:8099
    → if timeout: restart via elev.py
    → log action to memory/ops/incidents.jsonl
```

## Open Questions for Mechanic
1. Should collector be a single schtask hitting all 4 hosts sequentially, or 4 parallel tasks?
   (Sequential is simpler; parallel risks WinRM connection limits. Recommend sequential with 5s timeout per host.)
2. Where does the "stall" signal hand off to Verifier #3? Suggest: collector writes `memory/fleet/stall-signal.json`
   with `{timestamp, agents_with_zero_delta, consecutive_cycles}`; Verifier polls that file.
3. Should state_collector also trigger auto-remediation (e.g., unload model on OOM) or just alert?
   Recommend: alert-only in v1; remediation triggered by Orchestrator's remediation_policy.py reading the alert leaf.

## Confidence & Caveats
- Signal list is based on current cockpit API surface (/api/fleet/cockpit) and existing probe scripts.
- Threshold values are starting points, not validated; Mechanic should A/B test during first week of production.
- The "stall" definition (3 cycles = 15 min) assumes 5-min schtask interval; if interval changes, update N accordingly.
