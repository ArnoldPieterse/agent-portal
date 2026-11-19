# Builder assist: Mechanic Goal 8 - /api/fleet/status endpoint (2026-11-19)

## What was done
Implemented `_fleet_status()` function + `/api/fleet/status` route in agent_portal.py.

## Data contract (per goal spec)
Per host: {reachable, latency_ms, disk_pct, mem_pct, portal_up}
Plus: last_check timestamp, overall rollup (green/amber/red)

## Sources
- Reachability + latency: memory/mechanic/net_probe.state.json (fail_counts, latencies)
- Disk/mem: computed locally via shutil.disk_usage + GlobalMemoryStatusEx (serving host = "red")
- portal_up: True for local host (we're serving the request), null for remote

## Rollup rule (from Scribe forecast)
- red: portal_down OR >=2 hosts unreachable
- amber: any host unreachable OR disk>=85% OR mem>=90%
- green: all reachable + thresholds ok

## Verification
- py_compile PASS (agent_portal.py)
- Direct function call returns well-formed JSON with all 4 host keys (white/black/red/blue)
- In-sandbox result shows overall="red" (expected: net_probe.state.json has fail_count=4 for all hosts due to sandbox firewall - known limitation per Scribe forecast)
- Acceptance criterion (a) MET: endpoint returns well-formed JSON for all 4 host keys

## Remaining (host-gated, not blocked)
- Acceptance criterion (b): values correct against live probe - requires non-sandbox seat with fleet access
- UI status strip in ops tab (index.html/ui/core.js) - separate work item

## Artifact
agent_portal.py: _fleet_status() function (~50 lines) + route handler at /api/fleet/status
