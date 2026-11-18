# Design Forecast: Agent Fleet Overview Panel (Orchestrator Cycle-4 Goal #1)

Author: Designer seat. Date: 2026-11-18. Status: DRAFT for Builder implementation reference.

## Context
Orchestrator goal: /api/fleet/overview endpoint + card grid in fleet tab showing per-agent
model status, goal progress (open/closed), and capacity at a glance.
Existing foundation: cycle-3 fleet panel (topology view + status dots) is live in ui/app.css + core.js.
This forecast specifies the OVERVIEW PANEL as a new section above the topology view.

## Layout Spec

### Container
- .fleet-overview - full-width section at top of fleet tab, margin-bottom: var(--space-lg)
- CSS Grid: grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))
- Gap: var(--space-md) (8px)
- At 768px or below: single column stack

### Card Anatomy (.agent-card)
Each card = one agent. Structure top-to-bottom:
1. Header row: agent name (font-weight: 600, font-size: var(--text-sm)) + status dot (8px circle)
2. Model line: model alias in monospace, muted color (var(--text-muted)); "not_loaded" shown as italic
3. Progress bar: thin (4px height) rounded bar showing open/closed ratio; fill = var(--ok) when 100%, var(--warn) when >50%, var(--err) when <25%
4. Goal count: "7/10" in small text, right-aligned on progress bar row
5. Footer: capacity indicator (e.g., "3 tasks queued") or "idle" badge

### Status Dot Colors (use existing tokens - NO new hex values)
- Online + goals progressing: var(--ok)
- Online but idle/stale >60s: var(--warn)
- Not loaded / unreachable: var(--err)
- Offline (host down): var(--text-muted) with reduced opacity

### Interaction
- Hover: subtle lift (transform: translateY(-2px), box-shadow increase) - transition 150ms ease
- Click: navigate to that agent's detail (future; for now just visual affordance via cursor:pointer)
- No JS animation on load - cards appear in staggered fade-in (opacity 0->1, 200ms, 50ms stagger per card)

## Responsive Matrix
| Breakpoint | Columns | Card min-width | Notes |
|---|---|---|---|
| 1920px+ | 4 | 220px | Standard |
| 1024-1919px | 3 | 220px | Topology view shifts below |
| 768-1023px | 2 | 200px | Reduce card padding to var(--space-sm) |
| <768px | 1 | full-width | Stack; hide capacity footer (show on tap) |

## Token Compliance Checklist
- All colors: var() refs only (no hex in component rules)
- Spacing: var(--space-xs/sm/md/lg) scale
- Typography: var(--text-sm), var(--text-xs) - no new sizes
- Border-radius: var(--radius-sm) on cards, var(--radius-md) on progress bar
- Durations: 150ms hover, 200ms fade-in (use existing --dur-fast / --dur-med if defined, else inline)

## API Contract Expectation (for Builder to confirm)
```json
{
  "agents": [
    {
      "name": "designer",
      "model": "gpt-4o-mini",
      "status": "online|idle|not_loaded|offline",
      "goals_open": 3,
      "goals_total": 10,
      "queue_depth": 0,
      "last_active": "2026-11-18T14:32:00Z"
    }
  ],
  "fleet_summary": { "online": 7, "total": 8 }
}
```

## Anti-patterns to avoid
- Do NOT use the existing .fleet-loading spinner for this panel - it is a grid, not a list; use a skeleton card (3 cards with shimmer) instead
- Do NOT add a new color token; reuse existing --ok/--warn/--err palette
- Do NOT make cards equal height if content varies - use align-items: start

## Verification Acceptance (for Verifier)
1. Grep ui/app.css for hex colors in .agent-card rules -> 0 hits
2. Screenshot at 1920px, 1024px, 768px, 375px -> no overflow, correct column count
3. Network tab: single /api/fleet/overview call on panel load, no N+1 per-agent calls
