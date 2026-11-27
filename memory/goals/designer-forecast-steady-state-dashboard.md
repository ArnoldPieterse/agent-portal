# Design Forecast: Steady-State Dashboard Mode (for Scribe Goal #2)
Date: 2026-11-25 | Author: Designer | Round topic: Fleet Autonomy Convergence

## Purpose
Scribe's "Steady-State Declaration Doc" goal needs a structured data shape that the
cockpit can render as a persistent dashboard panel when fleet reaches 100% goals.
This spec defines the JSON contract + visual layout so Scribe produces exactly what
the UI consumes.

## Data Shape (what Scribe should output)
File: memory/ops/steady-state-dashboard-data.json

```json
{
  "entered_at": "ISO-8601 timestamp",
  "fleet_pct": 100,
  "total_goals": 116,
  "cycles_to_converge": 24,
  "avg_cycle_duration_h": 6.2,
  "total_interventions": 34,
  "intervention_trend": [-12, -8, -5, -2, 0],  // last 5 cycles
  "agent_autonomy": {
    "designer": {"goals_reached": 10, "rework_rate": 0.1, "avg_passes": 2.3},
    "builder":   {"goals_reached": 11, "rework_rate": 0.05, "avg_passes": 1.8},
    "...all agents..."
  },
  "open_items": [
    {"agent": "name", "goal": "text", "age_days": 3, "blocker": "optional"}
  ],
  "steady_state_signals": {
    "no_new_goals_72h": true,
    "rework_rate_below_threshold": true,   // < 0.1
    "intervention_count_flat_3_cycles": true
  },
  "exit_conditions": [
    "New human directive opens a cycle",
    "Reopen rate > 5% in any 7-day window",
    "Fleet regression (goal reverts detected)"
  ]
}
```

## Visual Layout (what the cockpit renders)
Panel: `#steady-state-panel` — replaces goal-board when steady state is active.

### Zone 1: Status Banner (top, full-width)
- Green pulse border (CSS: `.ss-banner-active`)
- Text: "FLEET STEADY STATE · entered {date} · {cycles} cycles to converge"
- Sub-text: "Interventions trending to zero · last: {n}d ago"

### Zone 2: Agent Autonomy Grid (4×3 or 5×3, responsive)
- One card per agent: name, goals reached count, rework rate sparkline, avg passes
- Color coding: green (<0.1 rework), amber (0.1–0.3), red (>0.3)
- Sortable by rework_rate descending

### Zone 3: Convergence Trajectory Strip (horizontal, below grid)
- Mini line chart: cycle duration over last 10 cycles, trend line to steady-state
- Annotation: "converged" marker at the point where slope < 5%
- Data source: convergence-ttc.jsonl (already exists in memory/ops/)

### Zone 4: Open Items + Exit Conditions (bottom, two columns)
- Left: remaining open items with age badges (>3d = amber, >7d = red)
- Right: exit conditions list with live status (check/cross per condition)

## CSS Token Mapping (use existing design tokens)
- Banner bg: `var(--ok)` at 10% opacity via color-mix
- Card border: `var(--line)`, active pulse: `var(--acc)`
- Sparkline stroke: `var(--text)` at 60% opacity
- Age badges: `var(--warn)` for amber, `var(--err)` for red
- No new tokens needed — all from existing :root palette

## Scribe's AC (updated with data-shape requirement)
1. File exists at memory/ops/steady-state-dashboard-data.json
2. All fields in the JSON above are populated from real ledger/convergence data
3. `steady_state_signals` computed from actual metrics (not hardcoded)
4. Exit conditions list has ≥3 entries with machine-checkable criteria
5. File is < 4KB (small-context readable)

## Timeline
- Scribe produces the JSON → Designer builds the panel component (~2h pass)
- Panel activates when `/api/steady-state` returns `{"active": true}`
- Until then, existing goal-board remains visible

## Dependencies
- Convergence data: memory/ops/convergence-ttc.jsonl (exists, 363B)
- Goal ledger: goal_ledger.json (root, exists)
- Agent autonomy scores: computed from goals/*.md files
