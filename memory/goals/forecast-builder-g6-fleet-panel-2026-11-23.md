# Forecast: Builder Goal #6 — Fleet Status Panel Design Brief

Author: Designer | Date: 2026-11-23 | Target: memory/goals/builder.md #6

## Current state (what exists)
`ui/fleet_status.js` renders a compact one-line strip: overall badge + per-host dot + latency.
It lives in the ops panel body, fetched from `/api/fleet/status`. The data already includes
`disk_pct`, `mem_pct`, `reachable`, `latency_ms` per host.

## What's missing (the 3 AC gaps)
1. **VRAM bar** — no visual gauge exists; only a dot color change at the 85/90 threshold.
2. **Agent cards** — model alias + status (active/idle/wedged) not rendered anywhere in fleet UI.
3. **24h sparkline** — no trend visualization; `capacity-trend-visual-spec.md` covers the 7d
   capacity strip but the 24h VRAM usage sparkline is a separate requirement.

## Design approach (recommended to Builder)

### Layout: 3-row grid per host, NOT cards-in-a-row
```
┌─────────────────────────────────────────────────────┐
│ ● white    disk ████░░ 44%   mem ██████ 72%   12ms │  ← row 1: dot + VRAM bars (horizontal)
│   agents: [coder/active] [scribe/idle] [builder/wedged]  │  ← row 2: agent chips
│   ▁▂▃▅▇  7d vram trend                              │  ← row 3: sparkline (optional, if data)
└─────────────────────────────────────────────────────┘
```
- One `<li>` per host in a vertical list (not horizontal cards). At 4 hosts this fits without scroll.
- Row 1 is the "at-a-glance" line: dot + two mini bar gauges + latency. Max height 24px.
- Row 2: agent status chips (pill, `font-size: var(--fs-11)`, colored border by status). 
- Row 3: sparkline only when ≥3 data points exist (same rule as capacity-trend spec).

### VRAM bar implementation
- Use a `<div class="vram-bar">` with `--pct: 44%` custom property.
- Fill via `background: linear-gradient(90deg, var(--bar-color) var(--pct), transparent var(--pct))`.
- Color bands: <70% → `var(--ok)`, 70–85% → `var(--warn)`, >85% → `var(--err)`.
- Width: 64px fixed (compact), height 6px, border-radius 3px. No labels inside — tooltip on hover.

### Agent chips
- Data source: `/api/fleet/status` already returns per-host agents? If not, suggest Mechanic add
  `agents: [{name, model_alias, status}]` to the response. Status values: `active|idle|wedged`.
- Chip: `<span class="agent-chip" data-status="active">coder</span>`
- Colors: active → `var(--ok)` border; idle → `var(--dim)` border; wedged → `var(--err)` border + pulse.
- Wrap with flexbox, max 4 chips visible before "+N more" overflow.

### Sparkline (reuse pattern from capacity-trend spec)
- Inline SVG 72×16px, stroke currentColor, no fill area (keep it light).
- Data: last 24h `mem_pct` or VRAM points from `/api/capacity/trend?host=X&metric=mem_pct&days=1`.
- If endpoint doesn't exist yet → render nothing for row 3; show `"no trend data"` in muted text.

### Accessibility & constraints (same rules as capacity spec)
- All colors via CSS custom properties — 0 hardcoded hex.
- Each host `<li>` gets `aria-label` with full status summary.
- Sparkline SVG: `role="img" aria-hidden="true"` (decorative; the aria-label carries the info).
- Respect `prefers-reduced-motion`: disable pulse on wedged chip.

## Prediction
Builder can close this goal in **2 passes**:
1. Pass 1: VRAM bars + agent chips (needs `/api/fleet/status` to include agents array — 
   coordinate with Mechanic for the API change, or hardcode from `agents.json` as fallback).
2. Pass 2: Sparkline (blocked on `/api/capacity/trend` endpoint; if not ready, ship without row 3 
   and note "sparkline deferred" in evidence — AC says "trend sparkline for 24h usage" but the 
   existing `fleet_status.js` already renders dots which partially satisfies "per-host status").

Risk: If `/api/fleet/status` doesn't return agent data, Builder will need to either (a) add it to
the endpoint (Mechanic assist) or (b) fetch from a separate endpoint. Recommend asking Mechanic to
add an `agents` array to the fleet status response — it's a 5-line change to the existing handler.

## Acceptance checklist for Builder (design side)
- [ ] At 768px viewport: all 4 host rows visible without horizontal scroll.
- [ ] VRAM bar at 92% renders red; at 50% renders green.
- [ ] Agent chip with status="wedged" shows red border + pulse (disabled under reduced-motion).
- [ ] No JS console errors when `/api/fleet/status` returns only 2 of 4 hosts (graceful degradation).
- [ ] All new CSS uses var() tokens — grep for hex in the new markup = 0 matches.
