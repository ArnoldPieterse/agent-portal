# Goal #4 - Load Baseline Day 2 (2026-11-17)

## What ran
- load_probe.py executed from Red seat (IP_RED) at 14:13 UTC
- Target: [LAN-IP]:8099 (White portal)
- Result: all 260 requests failed (timeout) - portal unreachable from Red

## Finding
The daily load probe MUST run from the White seat (where the portal listens). 
Remote seats have Windows firewall blocking outbound :8099. Day 1 baseline 
(2026-11-16, clean data) was collected from White.

## Next step
Run load_probe.py from White seat for day 3+ data. Need 7 total days + 
regression demo to close this goal.

## Artifact
memory/ops/load-baseline.jsonl (3 entries: day1 clean, day2 all-errors-from-red, diagnostic note)
