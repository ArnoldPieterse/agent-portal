# Fleet state + portal lifecycle — 2026-11-15 ~09:4x (Mechanic lane; Orchestrator round)

## State change vs 11-15 ~01:5x assumption ("all remotes powered down")
- **Red .245 is UP**: Studio :8888 answering (fleet probe state=idle, no models loaded — human unloaded it); SMB \\red\c$ reachable (memory_mirror 09:48:53 pushed 3 files OK).
- Pale .39 / Black .99: DOWN (fleet probe unreachable; SMB error 67 network name not found) — consistent with human power-down.
- White local: Studio :8888 busy during active chat turns (Qwen3.8-27B-Q8_0 resident); portal :8099 up.

## Portal lifecycle this round (planned maintenance, NOT outages)
- 5 restarts between ~09:31 and ~09:4x, each per runbook: taskkill old PID -> `schtasks /run /tn PortalRun` -> new PID on :8099 + CreationDate > agent_portal.py LastWriteTime -> ⚠missing:_portal_pid.txt updated. Each downtime ~10 s; GET /api/memory 200 after every restart.
- Current PID: **7032** (see _portal_pid.txt). Reason for restarts: pre-prune index gate + /api/ops tiles + /api/fleet 5s-budget fix landed in agent_portal.py.

## Runbook note (goal 1: outages restored <5 min)
- No unplanned outage occurred this round; planned restarts each restored service in ~10 s. If a future restart leaves :8099 dark >60 s, check portal_run_err.log then `schtasks /run /tn PortalRun` again (Status may have cleared to Ready after the kill).

## /api/fleet 5s-budget fix (discovered by Verifier cross-check)
- Pre-fix: sequential per-host probes (2 x 3 s sub-probes) with 3 dead remotes = up to ~18 s > panel's 5 s refresh window (cross-check FAILed at 5 s).
- Post-fix in agent_portal.py: parallel probes (ThreadPoolExecutor), FLEET_PROBE_TIMEOUT=2 s, negative dead-cache per host for FLEET_TTL=15 s, /v1/models fetched on 30 s TTL with last-known-list fallback (Studio's /v1/models stalls >2 s while a generation is active — observed 3.62 s). Result: cold snapshot ~2.0 s, warm ~0.1 s; cross-check PASS (memory/verifier/fleet_crosscheck_result.json).
