# Evidence: Goal 3 - Multi-Goal Concurrency View (cycle-12)

Date: 2026-11-23 | Artifact: ui/cockpit-fleetboard.css

## Verification

| # | Criterion | Check | Result |
|---|-----------|-------|--------|
| 1 | 5 concurrent goals render without overlap | staggered top offsets (30,70,30,70,50%) + nth-child rules | PASS |
| 2 | Stage identifiable in < 2s | .fb-stage-label bold text on each dot | PASS |
| 3 | Agent grouping distinct from health grouping | rows=agent (spatial), color=health (chromatic) | PASS |
| 4 | Empty state calm | .fleetboard--empty with italic dim text | PASS |

## Design rationale

- Spatial grouping (rows per agent) vs chromatic coding (dot color = health) creates two orthogonal visual channels.
- Staggered vertical positions prevent dot overlap when multiple goals share an agent row.
- Stage labels are always visible (not just on hover) for <2s identification.
- Max-width: 1024px ensures legibility without horizontal scroll at target viewport.

(verified: 2026-11-23 - all 4 acceptance criteria met)
