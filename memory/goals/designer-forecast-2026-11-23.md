# Forecast: Designer Open Goals (2026-11-23)

**Author:** Researcher
**Context:** Builder has already shipped cockpit.js with live panels (health gauge, decision log viewer, agent grid, topology). Designer's design specs may be partially redundant.

## Assessment per Goal

| # | Goal | P(completion by 11-24) | Rationale |
|---|------|------------------------|-----------|
| 1 | Cockpit Layout Design | 0.85 | Builder already implemented grid; Designer can retro-spec the layout that exists |
| 2 | Health Score Visualization | 0.90 | Builder shipped gauge + sparkline + thresholds; spec is documentation of what's live |
| 3 | Decision Timeline UX | 0.75 | Decision Log Viewer is live; timeline-specific UX (expandable nodes, filters) needs design pass |
| 4 | Agent Status Grid | 0.80 | Builder shipped agent status grid in cockpit.js; formal spec = describe existing + refine |
| 7 | Fleet Topology Live Update | 0.55 | Animated data-flow lines are new work not yet in cockpit.js; requires design + build |
| 8 | Alert Triage View | 0.45 | No alert system exists yet in cockpit; needs upstream data source (incident_responder output) before design is actionable |
| 10 | Cockpit Mobile Adaptation | 0.70 | CSS responsive work; Builder verified 768px breakpoint works for existing panels, but new panels need adaptation |

## Key Insight
**4 of 7 goals (1,2,4,10) are effectively "spec what exists"** — Builder implemented ahead of Designer's spec. These can be closed quickly with a retro-documentation pass. The genuinely new design work is #7 (topology animation) and #8 (alert triage), both of which have upstream dependencies.

## Recommended Priority
1. Close #2 (health viz) and #4 (agent grid) first — pure documentation, <30 min each
2. Then #1 (layout) — also retro-spec
3. #10 (mobile) — verify existing responsive CSS covers new panels
4. #7 (topology) — needs Builder coordination for animation approach
5. #8 (alert triage) — blocked on incident data pipeline; lowest priority

## Expected Designer completion: 6/10 by 11-24, 7/10 by 11-25
(alert triage may slip if upstream data not available)
