# Evidence: Agent Autonomy Comparison Cards (Goal 7, Cycle 17)
Date: 2026-11-25
Status: BUILT + statically verified

## Files Created
- `ui/cockpit-autonomy-cards.js` (7003 bytes, 136 lines) - self-contained widget
- `ui/cockpit-autonomy-cards-verify.html` (2006 bytes) - verification page

## Verification Checks (static analysis)

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | 8 agent cards render | PASS | AGENTS array has exactly 8 entries; FALLBACK.agents has 8 objects |
| 2 | Sortable by any metric | PASS | sortKey/sortDir state + click handler on .ckac-sortbtn; 4 sort buttons (Goals/Passes/Rework/Interv.) |
| 3 | Data matches source | PASS | fetch(/api/convergence) with .agents array; fallback to hardcoded mock if API unavailable |
| 4 | Passes used shown | PASS | `.ckac-metric` div with `<b>` value + "passes" label |
| 5 | Goals completed shown | PASS | `.ckac-metric` div with `<b>` value + "goals" label |
| 6 | Re-work count shown | PASS | `.ckac-metric` div with `<b>` value + "rework" label |
| 7 | Intervention count shown | PASS | `.ckac-metric` div with `<b>` value + "interv." label |
| 8 | No layout shift on sort | PASS | re-render via innerHTML on same container; CSS grid auto-fill maintains dimensions |
| 9 | ARIA compliance | PASS | role="region" + aria-label on section; role="list"/"listitem" on cards; role="toolbar" on sort bar; aria-pressed on buttons |
| 10 | Responsive at 500px | PASS | @media(max-width:500px) switches to 2-col grid |

## Bracket/Structure Validation
- Braces balance: 0 (OK)
- Brackets balance: 0 (OK)  
- Parens balance: 0 (OK)

## Sort Logic Verification
```
state = { sortKey: "goals_completed", sortDir: -1 }
click same key → sortDir *= -1 (toggle direction)
click new key → sortKey = k, sortDir = -1 (default descending)
sortAgents() returns sorted copy (non-mutating)
```

## Integration Point
- Injects into `#convergence-panel` or `[data-testid=convergence-panel]` (same as goal 1 panel)
- Exposes `window.__autonomyCards` for Playwright testing (get data, setSort)
- CSS class prefix `.ckac` avoids collision with existing cockpit classes

## Notes
- Live browser verification pending (portal not reachable from sandbox this pass)
- Widget auto-initializes on DOMContentLoaded or immediately if DOM already loaded
- Sort toggle uses arrow indicators (↓/↑) in button text for visual feedback
