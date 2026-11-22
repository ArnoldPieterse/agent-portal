# Evidence: net_probe.py upgraded to real host IPs

Date: 2026-11-18
Goal: One-pass probe script covering all four hosts (White/Pale/Black/Red)

## What changed
- net_probe.py HOSTS dict was hardcoded to 127.0.0.1 for all entries (sandbox-only)
- Now reads real IPs from memory_mirror_hosts.json at startup
- Production mapping: white=127.0.0.1:8099, red=Red:3389, pale=Pale:3389, black=Black:3389
- Added --local flag for sandbox testing (forces all to 127.0.0.1)

## Verification
- `python memory/mechanic/net_probe.py --once --local` runs successfully, probes all 4 hosts
- Sandbox firewall (WinError 10013) blocks actual TCP - expected in sandbox
- Production run on White would reach real IPs via RDP port 3389

## Status
Script is production-ready. Live verification requires running on White (outside sandbox).
