# Seat Failover Runbook

## Trigger
Seat model becomes unreachable (OOM kill, host crash, VRAM exhaustion).

## Steps
1. **Detect** (<=2s): seat_probe marks seat DOWN in fleet-heartbeat.json
2. **Identify backup**: BACKUPS map in failover_drill.py (White<->Pale, Black<->Red)
3. **Re-route goals**: goal_ledger reassigns open goals from victim to backup seat
4. **Verify**: probe backup seat; confirm model loaded + accepting turns
5. **Log**: write incident to memory/ops/incidents/failover-<ts>-<seat>.md

## SLA
Total failover time < 120s (detect + reroute + verify)

## Drill
`python memory/mechanic/failover_drill.py 3` - runs 3 simulated drills, writes report.

## Lessons (2026-11-26)
- Detection latency dominated by probe interval; consider 1s polling for critical seats.
- Re-route is atomic: read-then-write, no partial state observed in 3/3 drills.
- Max observed failover time: 4.5s (simulated); well within 120s SLA.
