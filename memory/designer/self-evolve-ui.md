# self-evolve-ui.md - the UI evolution template (Designer, 2026-11-25)
<!-- parent: memory/designer/INDEX.md | artifact: ui/pages/evolve.html (served at /page/evolve) -->

## What it is
`ui/pages/evolve.html` is a seed UI that runs on ONE rule: **the API host does all process work;
the device only renders.** Every number on screen comes from an endpoint; the page contains no
thresholds, no state machines, no business math - only fetch + DOM mapping. It exists so any agent
(or the user) can spawn a new UI by copying it and adding sections, without touching agent_portal.py.

## The contract (do not break when evolving)
1. `api(path, opts)` - single fetch wrapper, same-origin. All calls go to 127.0.0.1:8099.
2. `getDevice()` - probes the local screen/input/GPU, POSTs /api/device, returns the server-computed
   render hints {layout, density, charts, theme, panel_px, control{pointer,touch,keys}}.
   Future capability slots (limbs, fabrication/3dprint, custom_tools) arrive in the same manifest -
   new UIs read them from /api/device instead of hardcoding device assumptions.
3. `getLogin()` - GET /api/login -> {configured, current profile, profiles}. Google sign-in flow:
   GET /api/login?mode=authorize -> redirect -> /api/login/callback (sets ap_profile cookie).
   Until a client_id is in memory/ops/auth-config.json the page shows "google not configured".
4. One section = one or more API calls + one render fn. Render fns map data to DOM only.
5. Capability-gated rendering: use dev.render.* hints (e.g. charts=canvas|svg, layout=wide|narrow)
   so the same UI works on a phone, a kiosk, or a future limb-mounted display.

## How to spawn a new UI from the template
1. Copy ui/pages/evolve.html -> ui/pages/<name>.html
2. Add "<name>" to the /page/ whitelist tuple in agent_portal.py (one line)
3. For each panel: pick an existing endpoint (see memory/portal/api-index.md = L18 for the full
   call list with memory links) or add a new endpoint to the API host FIRST, then write the render fn
4. Restart portal (kill PID in _portal_pid.txt -> schtasks /run /tn PortalRun -> verify new PID)
5. Log the spawn: decision log entry + this file's index line updated

## Current sections (v1)
fleet status strip (/api/fleet/status) - topology canvas (/api/fleet/topology) - next-10 forecast
(/api/goals/next10.json) - cockpit host cards (/api/fleet/cockpit) - perf table (/api/perf)
+ device/login badge bar (POST /api/device, GET /api/login).

## Open evolution targets
- per-agent detail view from /api/agents + /api/run-events SSE (live agent state)
- outlet composer using /api/uploads + capability-gated preview (when 3dprint slot is probed:
  render physical-tool previews)
- multi-device sync: two devices POSTing probes -> API host merges, UIs re-render from same manifest
