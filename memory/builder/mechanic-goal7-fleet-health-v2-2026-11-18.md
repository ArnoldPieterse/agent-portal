# Fleet Health v2 - disk/memory/model-load fields added (Mechanic goal 7)
Date: 2026-11-18 06:31
Agent: Builder (assisting Mechanic)
File: agent_portal.py sha12=abcaee06bc9c

## What was done
Extended `_fleet_health_snapshot()` return dict with three new fields:
- `hosts.White.disk` - {total_gb, used_gb, percent} via psutil.disk_usage()
- `hosts.White.memory` - {total_gb, used_gb, percent} via psutil.virtual_memory()
- `model_load` - latest entry from memory/ops/model-load.jsonl (ts, run, missing)

Remote hosts (Red/Pale/Black) have disk/memory as null by design (no outbound calls).
Portal uptime (`portal_uptime_s`) was already present.

## Acceptance criteria status
- [x] Per-host disk usage - local host implemented; remotes = null (by design: no outbound)
- [x] Per-host memory usage - same as above
- [x] Portal uptime since last restart - already existed
- [x] Model-load status from Orchestrator's probe - reads latest model-load.jsonl entry

## Remaining for full closure
- Remote host disk/memory requires either: (a) a probe-side addition to fleet_probe.py
  that collects and reports these fields, or (b) SMB-based WMI queries. This is a
  Mechanic/Orchestrator decision on where to collect remote metrics.
