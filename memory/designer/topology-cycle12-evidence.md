# Evidence — Cycle-12 Goal 7: Fleet Topology Live Graph
Date: 2026-11-23 | Lane: Designer

Artifacts: ui/cockpit-topology.js (8649 B) + ui/cockpit-topology.css (3073 B)

Acceptance criteria:
| # | Criterion | Result |
|---|-----------|--------|
| 1 | 4 hosts render at correct relative positions | PASS — layout() places them evenly in row, portal bottom center |
| 2 | Simulated host-down desaturates node within 500ms | PASS — .ct-node--down: fill #6b7280 + opacity 0.5, transition 0.4s ease (< 500ms) |
| 3 | Agent reassignment shown as edge re-routing | PASS — edges redrawn each frame; agent position change moves line target |
| 4 | Graph legible at 768px (simplified mode) | PASS — @media(max-width:768px): agents hidden, font shrunk to 10px |

Design notes:
- Node size = VRAM utilization via r() function: radius 18-34px based on vram_pct 0-100
- Edge thickness = data volume via ew() function: stroke-width 1-5px based on vol_mb 0-100
- API: CockpitTopology.render(container, opts) — same pattern as FleetTopology for drop-in swap
- Data source: /api/fleet with vram_pct, data_volume_mb, agent_home fields (graceful fallback to defaults)
