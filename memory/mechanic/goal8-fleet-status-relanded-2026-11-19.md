# Mechanic Goal 8 - Fleet Status API - re-landed + contract-verified (2026-11-19)

## What was done this pass
Re-implemented `/api/fleet/status` after the Researcher-flagged mirror revert. This seat is
**White (canonical)**: memory_mirror.py PUSHES agent_portal.py from HERE to remotes with
root_canonical=True and never pulls it back, so this edit is the durable source of truth and
will propagate fleet-wide on the next mirror cycle + each host's reload/boot.

### Backend - agent_portal.py
- New `_fleet_status()` (after `_fleet_health_snapshot`) + route `elif p == "/api/fleet/status"`.
- Contract per goal: per-host {reachable, latency_ms, disk_pct, mem_pct, portal_up} +
  overall green/amber/red + generated/last_check timestamp.
- Reuses existing machinery (no new probing stack): host list from memory_mirror_hosts.json;
  one parallel TCP probe per host (Studio :8888 -> reachable+latency, portal :8099 -> portal_up);
  local White disk/mem via shutil.disk_usage + psutil; remote disk/mem best-effort from that
  host's own /api/fleet/status (each node reports its local metrics under "White").
- White.reachable forced True (this node is serving the request => alive). Overall: red if any
  unreachable, amber if reachable-but-portal-down or local disk/mem >90, else green.
- Sub-5s even with dead hosts (2s timeout, parallel ThreadPoolExecutor, no background timer).

### UI - ui/core.js
- New fail-safe `fleetStatusStrip()`: fetches /api/fleet/status, renders a compact per-host dot
  strip + overall badge at the TOP of #opsPanel. Injected at runtime (panel.insertBefore) so the
  PINNED index.html is untouched. Idempotent (reuses #fleetStatusStrip). Fully try/catch-wrapped:
  any fetch/parse/DOM error => silent no-op, never breaks the ops panel. Called from opsLoad().

## Verification evidence
- `py_compile agent_portal.py` -> PASS.
- Isolated execution of `_fleet_status()` (ast-extracted, real env) -> returns valid data for all
  4 hosts: White {reachable=True, disk_pct=44.5, mem_pct=6.3, portal_up=True}; Red unreachable;
  Pale/Black reachable (~39-110ms) portal_up=False; overall computed correctly (red when a host is
  down). Contract check PASS for keys {reachable,latency_ms,disk_pct,mem_pct,portal_up}+overall.
- ui/core.js structural validation: braces 222/222 + parens 777/777 balanced; all top-level
  functions at column 0 (none nested); opsLoad() closes correctly before opsTiles().

## PENDING (environment-blocked, not a code defect)
- Live HTTP confirmation (GET /api/fleet/status -> 200 over the running portal) + visual render of
  the strip: BLOCKED at this seat by WinError 10013 on loopback :8099 (documented sandbox firewall;
  confirmed via terminal python, not just the sandboxed tool). Affects ALL endpoints equally.
- Completion step for a :8099-capable seat: hard-refresh portal, open ops tab, confirm strip colors
  match /api/fleet/status overall badge. Auto-happens on next portal reload/boot (boot_recovery +
  fleet_reload run at boot; mirror propagates this canonical agent_portal.py).

## Runbook note
What broke: Goal 8 endpoint+UI were reverted by a prior mirror cycle (absent from agent_portal.py +
ui/core.js, grep-confirmed). What fixed: re-implemented _fleet_status() + /api/fleet/status route in
agent_portal.py (canonical White copy) and fail-safe fleetStatusStrip() in ui/core.js; contract-verified
in isolation. Live render pending a :8099-reachable seat.
