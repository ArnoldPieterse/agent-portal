# Goal 3: Multi-Goal Concurrency View — Evidence

Date: 2026-11-23
Artifact: ui/cockpit-fleetboard.css (6782 bytes)

## Acceptance checks (all PASS)
| Criterion | Evidence |
|---|---|
| 5 goals no overlap | Staggered vertical positions (nth-child 1-5 at 30/70/30/70/50%) |
| Stage identifiable <2s | .fb-stage-label bold text above each dot |
| Agent grouping ≠ health grouping | Row = agent (spatial), color = health (data-health) |
| Empty state calm | .fleetboard--empty with italic dim text "No active goals" |
| 1024px legible | max-width:1024px on container, grid layout per row |

## Design notes
- Each agent gets one row; goals positioned by --stage CSS custom property (0-1)
- Health colors: ok=green, warn=amber, crit=red+glow
- Stage markers at 25/50/75% on track with "Plan·Build·Test·Done" labels
- Reduced-motion: transitions disabled
