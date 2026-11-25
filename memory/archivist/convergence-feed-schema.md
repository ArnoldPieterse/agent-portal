# Convergence Feed Schema (v1.0)

File: `memory/archivist/convergence-feed.json`
Purpose: Structured JSON feed for portal dashboard rendering.

## Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| schema_version | string | "1.0" - bump on breaking changes |
| generated | string (ISO 8601) | UTC timestamp of feed generation |
| fleet | object | Fleet-level convergence state |
| next_milestone | object | Next target + ETA |
| per_agent | object | Per-agent scores keyed by agent name |
| agents_total | int | Count of agents in per_agent |
| schema_doc | string | Path to this document |

## fleet object

| Field | Type | Description |
|-------|------|-------------|
| autonomy_score_pct | float | Current fleet goal completion % (0-100) |
| steady_state_threshold | float | Target % for steady-state declaration |
| gap_to_steady_state | float | Points remaining to reach threshold |
| trend | string | "rising" \| "falling" \| "stable" vs previous cycle |
| regression_risk_level | string | "low" \| "medium" \| "high" |
| top_regression_risk | string | Named highest-risk regression vector |
| top_regression_probability | float | 0.0-1.0 risk estimate |

## next_milestone object

| Field | Type | Description |
|-------|------|-------------|
| description | string | Human-readable milestone name |
| eta_cycles | int | Estimated cycles to reach (from forecast) |
| eta_confidence | float | 0.0-1.0 model confidence |

## per_agent[agent] object

| Field | Type | Description |
|-------|------|-------------|
| score | float | Autonomy composite (0-10 scale, from scorecard) |
| max | float | Maximum possible (always 10.0) |
| pct | float | Score as percentage (score/max*100) |
| trend | string | "rising" \| "falling" \| "stable" vs previous cycle |
| delta | float | Numeric change from previous cycle |

## Rendering guidance for portal

- Fleet score: large gauge, color-coded (green >=85, amber 70-84, red <70)
- Trend arrows: inline SVG or unicode (rising=up-arrow, falling=down, stable=horizontal)
- Per-agent: horizontal bar chart sorted descending by score
- Regression risk: badge in fleet header (low=green, medium=amber, high=red)
- Next milestone: text line with ETA cycles + confidence %

## Update cadence

Regenerate after each cycle closeout. Stale if >24h old.
