# Seat Unreachable Runbook

## Trigger
Seat model fails to respond to health probe (3 consecutive failures).

## Steps
1. Confirm unreachable: `python memory/mechanic/seat_probe.py <seat>` returns DOWN
2. Check host reachability: ping / WinRM test
3. If host up but model down: restart model process on that seat
4. If host down: trigger failover (see seat-failover.md)
5. Log incident + update fleet-heartbeat.json

## SLA
Detection < 10s; recovery or failover < 120s
