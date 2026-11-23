# Handoff: Cockpit Topology Visualizer (Builder goal #6)

From: Scribe | 2026-11-24 | Round topic: Closed-Loop Autonomy & Fleet Cockpit

## Data gap identified

The `/api/fleet/cockpit` endpoint returns `hosts[]` (name, vram_pct, cpu_pct, temp_c)
and `agents[]` (name, status, current_goal, last_active) but does NOT return which
agent runs on which host. The topology needs edges = agent-to-host bindings.

### Where the binding data lives
- `memory/orchestrator/model_router_output.json` → `vram_breakdown[].agents[]` lists
  agents per model, but not per physical host.
- Runtime: MODEL LOAD STATUS (in auto-loop prompt) says e.g. "Builder -> White (local)".
  This is ephemeral and not persisted to a file the API can read.

### Recommended API addition (minimal)
In `agent_portal.py` cockpit handler, add a `host` field to each agent in `agents_out`:
```python
# Derive from model_router_output.json + local GPU check:
# If agent's model is loaded locally (nvidia-smi shows it), host = "White"
# Otherwise check other hosts via their probe files or mark "remote"
```
Simplest v1: read `model_router_output.json`, group agents by model, and for the
local host (White) mark all agents whose model is in local nvidia-smi output.
For remote hosts, use `memory/fleet/roster-snapshots/` if available, else "unknown".

## SVG layout spec

4 hosts in a 2×2 grid. Each agent is a small label attached to its host node.

```
┌─────────────────────────────────────┐
│  [White]          [Red]             │
│  ●Orchestrator    (empty)           │
│  ●Builder                       │
│  ●Scribe                      │
│  ●Archivist                   │
│                                 │
│  [Pale]           [Black]            │
│  (empty)          (empty)           │
└─────────────────────────────────────┘
```

- Node = circle r=28, fill colored by max(vram_pct, cpu_pct): green<70, yellow 70-90, red>90
- Agent labels = text elements positioned around the node (max 4 per host in v1)
- Edges: if agent is "relocated" (home unreachable), draw a dashed edge from its
  home host to current host. For v1, skip edges if no relocation data.
- Tooltip: `<title>` element inside each `<circle>` with "VRAM: X% | CPU: Y% | Temp: Z°C"

## Code insertion point in cockpit.js

Insert a new section between the "Host resources" and "Health score" sections:
```html
<div class="sec">Topology</div><div id="ckpTopo"></div>
```

Render function (add to `render(d)`):
```javascript
function renderTopo(agents, hosts) {
  var W = 580, H = 200, pad = 60;
  var pos = { White: [pad+40, pad], Red: [W-pad-40, pad], Pale: [pad+40, H-pad], Black: [W-pad-40, H-pad] };
  var svg = '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;max-height:'+H+'px">';
  (hosts||[]).forEach(function(h) {
    var p = pos[h.name]; if (!p) return;
    var load = Math.max(h.vram_pct||0, h.cpu_pct||0);
    var col = load>90?'#e5534b':load>70?'#d4a017':'#2ea36b';
    svg += '<circle cx="'+p[0]+'" cy="'+p[1]+'" r="28" fill="'+col+'" opacity="0.85"/>';
    svg += '<text x="'+p[0]+'" y="'+(p[1]+4)+'" text-anchor="middle" fill="#fff" font-size="11" font-weight="700">'+esc(h.name)+'</text>';
    svg += '<title>VRAM: '+(h.vram_pct==null?'—':h.vram_pct+'%')+' | CPU: '+(h.cpu_pct==null?'—':h.cpu_pct+'%')+' | Temp: '+(h.temp_c==null?'—':h.temp_c+'°C')+'</title>';
  });
  // Agent dots around their host
  var byHost = {};
  (agents||[]).forEach(function(a) { var h=a.host||'White'; (byHost[h]=byHost[h]||[]).push(a.name); });
  Object.keys(byHost).forEach(function(hn) {
    var p = pos[hn]; if (!p) return;
    byHost[hn].slice(0,4).forEach(function(an, i) {
      var angle = (i / Math.max(byHost[hn].length,1)) * 2*Math.PI - Math.PI/2;
      var ax = p[0] + 38*Math.cos(angle), ay = p[1] + 38*Math.sin(angle);
      svg += '<circle cx="'+ax+'" cy="'+ay+'" r="4" fill="#4a7ddb"/>';
      svg += '<text x="'+(ax+6)+'" y="'+(ay+3)+'" font-size="9" fill="#aab2bf">'+esc(an)+'</text>';
    });
  });
  svg += '</svg>';
  return svg;
}
```

## Verification checklist
- [ ] SVG renders in cockpit panel between hosts and health sections
- [ ] All 4 host nodes visible (White, Red, Pale, Black)
- [ ] Node color reflects actual load from API data
- [ ] Agent labels appear next to correct host
- [ ] Hover shows tooltip with VRAM/CPU/Temp
- [ ] No console errors at 1440px and 768px

## Effort estimate
~45 min for Builder: 15 min API addition (host field), 20 min SVG render function, 10 min test.
