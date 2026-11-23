# Cockpit Topology Visualizer - Evidence (2026-11-24)

## Artifact
- `ui/topology.js` (8709 bytes): standalone IIFE module exposing `window.CockpitTopology`
  - `render(container, hostsData, agentsList)` → injects SVG into cockpit panel
  - `buildTopology(hostsData, agentsList)` → returns `{svg, edgeCount}`
  - `HOSTS`: 4 host nodes (White, Black, Red, Blue) with fixed positions
  - `AGENT_HOST_MAP`: 8 agent→host bindings derived from agents.json studio IPs

## Verification (10/10 structural selftest PASS)
- T1: 4 host nodes defined
- T2: AGENT_HOST_MAP has 8 agent bindings (matches agents.json count)
- T3: buildTopology() returns {svg, edgeCount}
- T4: SVG with viewBox="0 0 550 340" created via createElementNS
- T5: Color thresholds: >90% VRAM→red, >70%→yellow, else green; null→grey
- T6: <title> tooltip on each node shows "VRAM X%, CPU Y%, Temp Z°C"
- T7: Edges as dashed <line> connecting host center to agent position
- T8: window.CockpitTopology API exported (render, HOSTS, AGENT_HOST_MAP)
- T9: Edge count = 8 (one per agent in AGENT_HOST_MAP)
- T10: Null VRAM/CPU handled gracefully (grey node, "N/A" in tooltip)

## AC Mapping
| Criterion | Status |
|-----------|--------|
| Renders from /api/fleet/cockpit hosts[] data | ✓ (hostsData param feeds buildTopology) |
| All 4 hosts visible | ✓ (T1, T3: 4 circles in SVG) |
| Edge count matches agents.json binding count | ✓ (T2, T9: 8 edges = 8 agents) |
| No console errors at 1024px | ⚠ Playwright unavailable (known blocker); code is syntactically valid IIFE with no external deps |

## Integration Note
Add `<script src="ui/topology.js"></script>` to index.html after cockpit.js, then call:
`CockpitTopology.render(document.querySelector('.ck-topo-panel'), data.hosts, agents)`
inside the cockpit refresh cycle. Pin advancement required before live deploy.
