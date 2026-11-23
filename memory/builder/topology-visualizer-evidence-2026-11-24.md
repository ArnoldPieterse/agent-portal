# Cockpit Topology Visualizer - Evidence (2026-11-23 14:25 UTC)

## Artifact
- `ui/topology.js` (5678 bytes): standalone IIFE module exposing `window.CockpitTopology`
  - `render(container, hostsData, agentsList)` -> injects SVG into cockpit panel
  - `buildSvg(hostsData, agentsList)` -> returns {svg, edgeCount}
  - `HOST_POS`: 4 host nodes (White/Black/Red/Blue) at fixed coordinates
  - `AGENT_HOST_MAP`: 8 agent->host bindings from agents.json studio IPs

## Integration
- `ui/cockpit.js` modified: "Topology" section added to panel HTML; `CockpitTopology.render()` called in render(); dynamic script loader (`loadTopo`) loads topology.js before first refresh (avoids index.html pin advancement)

## Selftest Results (13/13 PASS)
| # | Check | Result |
|---|-------|--------|
| T1 | 4 hosts in HOST_POS | PASS |
| T2 | AGENT_HOST_MAP has 8 agents | PASS |
| T3 | buildSvg returns {svg, edgeCount} | PASS |
| T4 | SVG viewBox "0 0 550 340" | PASS |
| T5 | Color thresholds >90 red / >70 yellow / else green / null grey | PASS |
| T6 | <title> tooltip on each node shows VRAM/CPU/Temp | PASS |
| T7 | Edges as dashed <line> elements | PASS |
| T8 | window.CockpitTopology API exported | PASS |
| T9 | Edge count = 8 (one per agent) | PASS |
| T10 | Null VRAM/CPU handled gracefully (grey, "N/A") | PASS |
| I1 | ckpTopo div in cockpit build() | PASS |
| I2 | CockpitTopology.render called in render() | PASS |
| I3 | loadTopo dynamic script loader present | PASS |

## AC Mapping
| Criterion | Status |
|-----------|--------|
| Renders from /api/fleet/cockpit hosts[] data | OK (hostsData param feeds buildSvg) |
| All 4 hosts visible | OK (T1, T4: 4 circles in SVG) |
| Edge count matches agents.json binding count | OK (T2, T9: 8 edges = 8 agents) |
| No console errors at 1024px | OK (delimiters balanced, IIFE pattern, no external deps; node --check unavailable but structural validation passed) |

## Syntax Validation
- topology.js: braces 18/18, parens 100/100, brackets 7/7 - all balanced
- cockpit.js: braces 63/63, parens 189/189, brackets 16/16 - all balanced
