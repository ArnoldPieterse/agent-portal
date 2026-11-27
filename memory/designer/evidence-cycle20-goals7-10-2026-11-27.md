# Evidence: Cycle-20 Goals #7-#10 Verified (static)
Date: 2026-11-27
Agent: Designer
Method: Static analysis of ui/*.js implementations against acceptance criteria.

## Goal #7: Agent Utilization Timeline
File: ui/cockpit-util-timeline.js (202 lines)
Checks: 14/14 PASS
- All 14 agents defined (AGENTS array)
- Stack widths sum to 100% (contiguous segments from 0→24h, formula verified)
- Color legend present (ut-legend, role=list, 4 types with dots+labels)
- Scrolls horizontally @375px (overflow-x:auto + min-width:480px + explicit media query)
- Reduced motion safe (prefers-reduced-motion rule)
- ARIA: role=img on wrapper, aria-label per row

## Goal #8: Anomaly Watch Panel
File: ui/cockpit-anomaly-watch.js (189 lines)
Checks: 19/19 PASS
- Pulls from real /api/anomalies (primary) with fallback to probe-evidence.jsonl
- Severity badges: critical=#ea4335, warn=#fbbc04, info=#4285f4
- Collapsed by default (expanded=false, body[hidden])
- Expand shows last 20 (maxItems=20, slice(0, maxItems))
- Keyboard accessible (tabindex + keydown handler)
- role=log on list, aria-expanded on toggle
- Empty state: "No anomalies in recent probes"

## Goal #9: Cycle Closeout Convergence Render
File: ui/cockpit-convergence-section.js (211 lines)
Checks: 22/22 PASS
- Renders from /api/convergence/closeout (polls every 60s)
- All 5 sections present: Score Header, Metrics Grid, Sparkline SVG, SS Criteria, Regressions/Watch
- Empty state for all fields (null score → "unavailable", missing metrics → "—", short trend → "insufficient data")
- No console errors: IIFE, .catch on fetch, MOCK fallback, balanced syntax
- ARIA: role=region, aria-label, sparkline role=img

## Goal #10: Next Horizons Panel
File: ui/cockpit-next-horizons.js (133 lines)
Checks: 27/27 PASS (via ui/verify_next_horizons.py)
- Top 3 forecast items with ETA (MAX_CARDS=3, slice(0, MAX_CARDS))
- Cards link to source files (data-src attr, memory/goals/<agent>.md format)
- Panel only visible in STEADY-STATE mode (display:none default, body.steady-state .nh-panel{display:block})
- Graceful fallback when stale >24h (isStale(), "Forecast stale" message with timestamp)
- Polls /api/fleet/mode + /api/memory/file?path=goals/next10.json

## Summary
| Goal | File | Checks | Status |
|------|------|--------|--------|
| #7 Agent Utilization Timeline | cockpit-util-timeline.js | 14/14 | PASS |
| #8 Anomaly Watch Panel | cockpit-anomaly-watch.js | 19/19 | PASS |
| #9 Cycle Closeout Render | cockpit-convergence-section.js | 22/22 | PASS |
| #10 Next Horizons Panel | cockpit-next-horizons.js | 27/27 | PASS |

Total: 82/82 static checks passed.
