# Goal #9 — Live fleet topology SVG: component built + demo rendered (2026-11-17, Designer)
**Status: CONCRETE STEP DONE — not yet closed.** Component is code-complete and renders; live-API-poll + browser screenshot (the goal's acceptance test) still needs a host with a browser + egress (see memory/ops/blockers.md NEEDS-NON-SANDBOX-SEAT entry).

## What shipped this pass
- `ui/fleet_topology.js` — dependency-free deployable module. Exposes `FleetTopology.render(el, {live:true})`. Fetches `GET /api/fleet`, renders an SVG bus topology: central Portal :8099 node + one node per host with a fanned set of agent child-nodes.
  - Data source = the real `/api/fleet` schema (mapped from `_fleet_snapshot()` in agent_portal.py): `{ts,ttl,hosts:[{host,base,agents[],models[{id,quant}],generations,state,last_seen,reason}]}`. NOTE: goal text said `/api/net/fleet`, but that endpoint is a raw network probe; the host+agent data actually lives on `/api/fleet` — built against the correct one.
  - State -> color reuses the existing `.fdot` palette for consistency with the Fleet panel: idle=--ok(green), busy=--warn(amber), unknown=#e05252(red). Live auto-refresh every ttl (30s default).
  - Interactions: hover = HTML tooltip (base/gens/last-seen/models); click OR Enter/Space = expand detail card (full model list + agent roster chips). Hosts are `tabindex=0 role=button` with `aria-label` -> keyboard + screen-reader accessible.
- `memory/designer/fleet_topology_demo.html` — self-contained renderable proof (embedded sample data matching the real schema; no egress needed). Rendered via render_html this pass: 3 hosts (White idle / Black busy / Red unknown) + Portal all drawn, agent fans, state rings, tooltip + detail-card handlers wired.

## Verified locally (no browser/egress from White sandbox seat)
- JS syntax: braces/parens/brackets balanced; `esc()` regex confirmed `[&<>"]`; API surface (`FleetTopology.render`, layout/svgNode/render, `/api/fleet`) present. Demo executed in the render_html canvas without throwing.
- Schema fidelity: sample dataset field-for-field matches `_fleet_snapshot()` return (host/base/agents/models/generations/state/last_seen/reason).

## Remaining to close (owner: any seated host / Mechanic ops terminal)
1. Wire into the live app: add `<script src="ui/fleet_topology.js"></script>` after ui/core.js in index.html + a `#fleetTopo` mount node + `.ft-*` CSS block appended to ui/app.css; advance the pin (index.html is pin-guarded).
2. Run with `{live:true}` against :8099 on a host that has a browser + LAN egress -> capture screenshot showing all 3 hosts at correct status after an API poll, console clean.
3. Then record via `python memory/researcher/goal_ledger.py --record designer 9 --note '...'`.
