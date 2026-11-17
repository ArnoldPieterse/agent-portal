# Goal #4 Status — Portal Load Test (2026-11-17)

**Seat**: Red (192.168.1.245) sandbox
**Status**: IN PROGRESS — 1/7 good baseline days collected

## What works
- `load_probe.py` functional (proven by 2026-11-16T18:37:54 entry: p50=127ms@10c, 373ms@50c, 1666ms@200c)
- Script updated 2026-11-17: added `--seat` and `--target` CLI params for multi-seat operation
- Baseline file at `memory/ops/load-baseline.jsonl` (4 entries, only 1 valid)

## What's blocking
- Portal runs on White (192.168.1.179:8099); this seat is Red
- Red sandbox firewall blocks outbound :8099 to White (WinError 10013 WSAEACCES)
- Probe MUST run from White seat where localhost:8099 is the portal

## To close (acceptance: one week baseline + regression demo)
1. Daily schtask on White running `python load_probe.py --seat white-sandbox` at fixed time
2. 7 consecutive days of data in load-baseline.jsonl
3. One regression caught (p95 > 1.3x trailing median) — can be simulated by adding artificial latency or testing under degraded conditions

## New finding (2026-11-17)
- Pale .39:445 now OPEN from Red sandbox (was reported down in hot notes) — may unblock additional probe targets

---
One-line runbook: load_probe.py requires White seat for :8099; remote seats get WSAEACCES. Use `--target` + firewall exception or run locally on White.
