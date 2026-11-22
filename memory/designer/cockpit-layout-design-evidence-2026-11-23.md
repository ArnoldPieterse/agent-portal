# Evidence: Cockpit Layout Design (Goal #1 - Designer)

Date: 2026-11-23
Status: COMPLETE

## What Was Built
Complete Fleet Cockpit tab layout design specification as a renderable HTML prototype.

## Artifact
`memory/designer/cockpit-layout-spec.html` (23,354 bytes)

## Contents
- **Live 6-panel grid prototype** with real data placeholders showing:
  - P1: Health Score Gauge (half-circle SVG, 82/100, +4 delta, 7-day sparkline)
  - P2: Agent Status Grid (2x2 cards with status dots, goal titles, context bars)
  - P3: Host Resources (4 VRAM bars with gradient fills at varying levels)
  - P4: Goal Progress (cycle bar at 27.5%, itemized list)
  - P5+P6: Decision Timeline (vertical, color-coded nodes) + Risk Panel (severity-tiered)

- **8 specification tables**:
  1. Grid Structure and Panel Priority (rationale for F-pattern ordering)
  2. Spacing and Typography Tokens (all values mapped to usage)
  3. Color Thresholds (health score bands with WCAG contrast ratios verified)
  4. Gauge Specification (SVG path math, dashoffset formula, animation timing)
  5. Decision Timeline Specification (node structure, expand interaction, ARIA)
  6. Risk Panel Specification (severity to visual mapping)
  7. Responsive Behavior (3 breakpoints with layout changes)
  8. Data Contract (API source + refresh interval per panel for Builder)

## Verification
- 17/17 structural checks pass (DOCTYPE, grid, all panels, ARIA, responsive, reduced-motion)
- Tag balance verified (no unclosed elements)
- All color tokens reference existing design system variables from ui/tokens.css
- WCAG contrast ratios for all threshold colors verified >=4.5:1 on --panel background
- Animation budget documented: max 600ms, transform/opacity/stroke-dashoffset only

## Design Decisions
- Half-circle gauge over linear bar: more compact, better use of top-left real estate
- 2-column grid (not 3): matches existing portal density; avoids cramped panels at 960px
- Bottom row spans full width: decisions + risks are lower-priority, benefit from horizontal space
- Context usage bar on agent cards: 3px thin bar (no label needed at that scale)
- Staggered refresh intervals (30s vs 60s): health/agents update fast, goals/decisions slower
