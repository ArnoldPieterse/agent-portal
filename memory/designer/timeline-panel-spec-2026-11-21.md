# Timeline Panel UI Spec — Designer contribution to Scribe Goal 1 (Temporal Query API)
Date: 2026-11-21
Status: DRAFT (ready for Scribe/Builder to implement once /api/timeline is live)

## Purpose
Render the JSON response from `GET /api/timeline?date=YYYY-MM-DD` as a compact
daily-activity strip in the portal's Activity tab. Also support compare mode
via `GET /api/timeline/compare?from=DATE&to=DATE`.

## Layout (768px–1200px)

### Single-day view (`/api/timeline?date=`)
```
┌─────────────────────────────────────────────────────┐
│ [◀] 2026-11-21 [▶]          (nav arrows, 44px tgt) │
├─────────────────────────────────────────────────────┤
│ Active Goals: 5 open / 3 closed today              │
├─────────────────────────────────────────────────────┤
│ Agent States (horizontal scroll if >6):            │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│ │ 🟢  │ │ 🟡  │ │ 🔴  │ │ ⚪  │ │ 🟢  │  ...     │
│ │Orch │ │Scrib│ │Mech │ │Arch │ │Rese │          │
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │
├─────────────────────────────────────────────────────┤
│ Recent Events (max 5, newest first):               │
│ • 14:32 Mechanic closed goal #3 (WinRM probe)     │
│ • 13:01 Scribe wrote weekly digest W46            │
│ • 11:45 Designer verified a11y tree PASS          │
└─────────────────────────────────────────────────────┘
```

### Compare view (`/api/timeline/compare?from=&to=`)
Two-column diff layout:
- Left column: "From" date summary (goals_opened, goals_closed, agents_changed)
- Right column: "To" date summary
- Middle: delta badges (+N / -N) with color coding
  - Green: net positive (more closed than opened)
  - Red: net negative
  - Neutral: no change

## Design Tokens
| Token | Value | Usage |
|-------|-------|-------|
| `--tl-bar-height` | 48px | Agent state card height |
| `--tl-event-gap` | 6px | Vertical gap between event rows |
| `--tl-date-nav-size` | 44px | Touch target for date arrows |
| `--tl-max-events` | 5 | Visible events without scroll |

## ARIA / Accessibility
- Date nav: `role="navigation"`, `aria-label="Timeline date navigation"`
- Agent cards: `role="listitem"`, `aria-label="{agent} status: {state}"`
- Event list: `<ol>` with `aria-label="Recent events for {date}"`
- Compare delta: `aria-live="polite"` so screen readers announce changes

## Animation
- Date navigation: 200ms ease slide (left/right) — respect `prefers-reduced-motion`
- Agent card status dot: 2s pulse loop (same as fleet panel)
- Event list items: staggered fade-in, 100ms delay per item, max 500ms total

## Data Mapping (JSON → DOM)
```
{active_goals[]}    → goal count badges + mini progress bar
{recent_events[]}   → <ol> event list (timestamp, agent, summary)
{agent_states{}}    → horizontal card strip (one per agent)
```

## Compare Mode Mapping
```
{goals_opened}      → left/right counters with delta badge
{goals_closed}      → same pattern
{events_added}      → single delta number
{agents_changed[]}  → chip list with before→after state icons
```

## Implementation Notes for Builder
- New file: `ui/timeline.js` (IIFE, no external deps)
- CSS in `ui/app.css` under `.tl-*` prefix
- Hook into existing tab system (Activity tab, sub-panel)
- Use `UI.skeleton()` for loading state, `UI.emptyState()` when no data
- Date picker: native `<input type="date">` styled to theme tokens

## API Response Schema (from `memory/scribe/timeline.py`)

`GET /api/timeline?date=YYYY-MM-DD` returns:

```json
{
  "date": "2026-11-21",
  "events": [
    {
      "date": "2026-11-21",
      "title": "LEVEL COUNTER + per-level change report 2026-11-20 ~22:3x",
      "preview": "Status: **DONE + live** - user request: persistent fleet level counter..."
    }
  ],
  "agent_snapshots": {
    "orchestrator": {
      "snapshot_date": "2026-11-20",
      "file": "memory/goals/archive/orchestrator-2026-11-20.md"
    }
  },
  "goal_files_available": ["archivist", "builder", "designer", "mechanic", "orchestrator", "researcher", "scribe", "verifier"]
}
```

### Field notes for UI
| Field | Type | UI mapping |
|-------|------|-----------|
| `date` | string (ISO) | Header date label |
| `events[]` | array (max 10) | Event list (show top 5, "Show more" for rest) |
| `events[].title` | string | Bold event heading |
| `events[].preview` | string (200 char truncation) | Muted subtitle text, clamp to 2 lines |
| `agent_snapshots` | object keyed by agent name | Agent state cards (use snapshot_date proximity for color: <7d=green, 7-30d=amber, >30d=grey) |
| `goal_files_available` | string[] | Context only; not directly rendered |

### Compare endpoint (planned, not yet implemented)
`GET /api/timeline/compare?from=DATE&to=DATE` — Scribe will add; UI spec above still applies for the two-column diff layout.

### Implementation target
- File: `ui/timeline-panel.js` (new)
- CSS: `ui/app.css` (append `.tl-*` classes using tokens above)
- Mount point: Activity tab, below existing activity feed
- JS entry: `renderTimelinePanel(dateStr)` exported for core.js to call on tab switch
