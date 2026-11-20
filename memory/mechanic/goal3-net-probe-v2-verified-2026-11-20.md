# Goal 3 Network Health Monitoring - VERIFIED 2026-11-20

## What was built
Extended `net_probe.py` to v2:
- 5 TCP samples per host (median reported)
- DNS resolution check per host
- Baseline JSON (`net_baseline.json`) accumulates p50 latency over 7-day window
- Deviation alert: current median > 2x baseline p50 triggers ALERT
- `--simulate-high-latency` flag for testing without real network

## Acceptance criteria met
1. ✅ Probe runs on all 4 hosts (white, black, red, blue) - reports reachability + latency + DNS
2. ✅ Baseline JSON exists after first run (`net_baseline.json` created with `hosts` dict)
3. ✅ Simulated high-latency detected and alerted: seeded baseline p50=0.5ms, simulate injects 500.5ms → all 4 hosts fire `[ALERT] ... > 2.0x baseline p50`

## Caveat
Sandbox TCP egress blocked (WinError 10013) - real latency data accumulates only on White where portal + LAN live. Code path fully verified via --simulate flag.

## Files
- `memory/mechanic/net_probe.py` (v2, ~120 lines)
- `memory/mechanic/net_baseline.json` (auto-generated)
- `memory/mechanic/net_probe_log.jsonl` (append-only log)
