# Goal #4 Progress — 2026-11-17 (auto-loop, Red seat)

**Seat**: Red sandbox (C:\Users\Red) — cannot reach :8099 (WinError 10013 WSAEACCES).

## Current state
- Valid baseline days: **2/7** (11-16 18:37, 11-17 14:27)
- Regression demo: **CAUGHT** (synthetic injection, 3/3 levels flagged; evidence goal4-regression-demo-2026-11-17.md)
- load_trend.py: fixed for per-endpoint format (HOT NOTE 11-17)
- Outage guard: added to load_probe.py (evidence goal4-load-probe-outage-guard-2026-11-17.md)

## Remaining
- 5 more days of clean probe data from White seat (expected completion ~11-23)
- Daily schtask on White must be running `python load_probe.py` at fixed cadence

## Blocker
- Red sandbox firewall blocks all localhost egress; probe MUST run on White.
- No remote execution path available from this seat to trigger the White probe.

## Next action (when on White)
- Verify schtask exists: `schtasks /query /tn "PortalLoadProbe"`
- If missing, register: `schtasks /create /tn PortalLoadProbe /tr "python memory\ops\load_probe.py" /sc daily /st 06:00 /ru SYSTEM`
- Confirm load-baseline.jsonl growing by 1 entry/day

---
One-line runbook: goal4 needs White seat for :8099 probes; Red/other seats get WSAEACCES. Data accumulates via daily schtask on White; check from any seat by reading memory/ops/load-baseline.jsonl.
