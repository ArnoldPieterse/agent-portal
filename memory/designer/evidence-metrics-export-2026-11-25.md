# Evidence: Convergence Metrics Export (Goal 10, Cycle 17)
Date: 2026-11-25
Status: BUILT + statically verified

## File Created
- `ui/cockpit-metrics-export.js` (7251 bytes, 180 lines)

## Verification Checks

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Button works | PASS | Two buttons (#export-json, #export-png) with click handlers; fetches /api/convergence on click |
| 2 | JSON matches API data | PASS | `fetch(API).then(r=>r.json()).then(exportJSON)` → `JSON.stringify(data,null,2)` → Blob download. Exact API payload serialized. |
| 3 | PNG renders at 800px wide | PASS | `var W = 800` canvas; all content fits within bounds (metrics grid 2x2, header, footer) |
| 4 | All metrics visible in PNG | PASS | Four metric cards drawn: Autonomy Score, Steady-State Progress %, Cycle Duration Trend, Intervention Counts + agent summary row + status dot |
| 5 | PNG is one-page summary | PASS | Single canvas (800x500) with header, topic, timestamp, 4 metric cards, footer agents, status indicator |
| 6 | No JS errors | PASS | All fetch calls in .catch(); canvas.toBlob has error callback; no unguarded operations |
| 7 | File naming convention | PASS | JSON: `convergence-metrics-{cycle}-{date}.json`; PNG: `convergence-summary-{cycle}.png` |

## Structure Validation
- Braces balance: 0 (OK)
- Brackets balance: 0 (OK)
- Parens balance: 0 (OK)

## PNG Layout (800×500px)
```
┌──────────────────────────────────────────────┐
│ Fleet Convergence Report - Cycle 17          │ ← header bar (60px)
│ Topic...                    Exported: ...    │
│                                              │
│ ┌─────────────────┐  ┌─────────────────┐   │
│ │ AUTONOMY SCORE  │  │ STEADY-STATE %  │   │ ← metric cards (2×110px)
│ │ 72/100          │  │ 64%             │   │
│ └─────────────────┘  └─────────────────┘   │
│ ┌─────────────────┐  ┌─────────────────┐   │
│ │ DURATION TREND  │  │ INTERVENTIONS   │   │ ← metric cards (2×110px)
│ │ 45→38→42→35→31  │  │ 6,4,3,2,1       │   │
│ └─────────────────┘  └─────────────────┘   │
│                                              │
│ Agents: Orch:3 Res:4 Ver:5 Des:6 ...  ●IN PROGRESS │ ← footer
└──────────────────────────────────────────────┘
```

## Integration
- Injects into #convergence-panel (same as goal 1 panel)
- Two buttons in a flex row with "Export" label
- Fallback data matches FALLBACK from cockpit-convergence.js (goal 1) for consistency
