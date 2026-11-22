# Fleet Panel Visual Design Spec (Goal #2)

Date: 2026-11-23
Status: SPEC COMPLETE — implementation in ui/fleet_status.js, ui/fleet_health.js, ui/app.css

## Overview

The Fleet tab renders a two-tier panel: **Hosts** (top row) and **Agents** (below).
At 1200px viewport the full layout must fit without horizontal scroll.

## Layout Grid

```
+------------------------------------------------------------------+
| FLEET HEALTH  [composite bar]    [last-update timestamp]          |
+------------------------------------------------------------------+
| HOST ROW (4 cards, equal width, gap 8px)                          |
| +----------+ +----------+ +----------+ +----------+              |
| | White    | | Black    | | Red      | | Blue     |              |
| | [dot]    | | [dot]    | | [dot]    | | [dot]    |              |
| | VRAM bar | | VRAM bar | | VRAM bar | | VRAM bar |              |
| | spark    | | spark    | | spark    | | spark    |              |
| +----------+ +----------+ +----------+ +----------+              |
+------------------------------------------------------------------+
| AGENT GRID (2 rows × 4 cols, gap 8px)                             |
| +--------+ +--------+ +--------+ +--------+                      |
| | Orch.  | | Resea. | | Design | | Build  |                      |
| | [dot]  | | [dot]  | | [dot]  | | [dot]  |                      |
| | goal   | | goal   | | goal   | | goal   |                      |
| +--------+ +--------+ +--------+ +--------+                      |
| +--------+ +--------+ +--------+ +--------+                      |
| | Verif. | | Archi  | | Scrib  | | Mech   |                      |
| | [dot]  | | [dot]  | | [dot]  | | [dot]  |                      |
| | goal   | | goal   | | goal   | | goal   |                      |
| +--------+ +--------+ +--------+ +--------+                      |
+------------------------------------------------------------------+
```

## Component Specs

### 1. Host Card (`.fh-host`)

| Property | Value |
|----------|-------|
| Width | `calc(25% - 6px)` in a 4-col grid |
| Min-height | 72px |
| Background | `var(--panel)` |
| Border | 1px solid `var(--line)`, radius `var(--br-md)` |
| Padding | `var(--sp-8)` |

**Status dot** (top-right of card):
- Active/healthy: `var(--ok)` with 2s pulse animation (`@keyframes fh-pulse`)
- Idle: `var(--dim)`, no animation
- Wedged/critical: `var(--err)` with 1.5s flash (`@keyframes fh-flash`)
- Size: 8px circle

**VRAM bar**:
- Track: 4px height, `var(--bg)`, radius 2px
- Fill: linear-gradient left-to-right from `var(--ok)` → `var(--acc)` at <70%, shifts to `var(--warn)` at 70–85%, `var(--err)` at >85%
- Transition: width 300ms ease (reflects live value changes)

**Sparkline** (optional, below VRAM bar):
- Inline SVG, 60×16px
- Path stroke: `var(--acc)`, 1.5px, no fill
- Data: last 20 health scores at 10s intervals
- Tooltip: `<title>` element inside SVG (native browser tooltip)

### 2. Agent Card (`.fh-agent`)

| Property | Value |
|----------|-------|
| Width | `calc(25% - 6px)` in a 4-col grid |
| Min-height | 56px |
| Background | `var(--panel)` |
| Border | 1px solid `var(--line)`, radius `var(--br-md)` |
| Padding | `var(--sp-8)` |

**Status dot** (left of name):
- Active: `var(--acc)` pulsing
- Idle/loading: `var(--warn)` static
- Error: `var(--err)` flashing

**Agent name**: font-size `var(--fs-12)`, font-weight 600, color `var(--text)`

**Current goal title**: font-size `var(--fs-11)`, color `var(--dim)`, single-line ellipsis (`overflow:hidden; text-overflow:ellipsis; white-space:nowrap`)

### 3. Composite Health Bar (`.fh-composite`)

- Full-width horizontal bar, 6px height
- Fill gradient: left-to-right, color determined by composite score tone
  - ≥80: `var(--ok)`
  - 50–79: `var(--warn)`
  - <50: `var(--err)`
- Label "Fleet Health" above, score number right-aligned

### 4. State Indicators (loading / empty / error)

Already implemented in ui/app.css (`.fleet-loading`, `.fleet-empty`, `.fleet-error`):
- Loading: centered spinner (`.fspin` keyframe, 0.7s rotation)
- Empty: SVG icon + guidance text, opacity 0.5
- Error: left-border banner, `var(--err)` border + tint background

## Animation Tokens

| Keyframe | Duration | Usage | Reduced-motion |
|----------|----------|-------|----------------|
| `fh-pulse` | 2s infinite | Active dot scale 1→1.4→1 | disabled (static) |
| `fh-flash` | 1.5s infinite | Error dot opacity 1→0.3→1 | disabled (solid red) |
| `fspin` | 0.7s linear | Loading spinner rotation | disabled (static icon) |

All animations are inside `@media (prefers-reduced-motion: no-preference)` guard.

## Color Thresholds (VRAM / Resource Bars)

| Range | Gradient | Token pair |
|-------|----------|------------|
| 0–69% | green → accent | `var(--ok)` → `var(--acc)` |
| 70–84% | amber → red | `var(--warn)` → `var(--err)` |
| 85–100% | solid red | `var(--err)` |

## Overflow Guard (1200px)

- Host grid: `display:grid; grid-template-columns:repeat(4,1fr); gap:8px`
- Agent grid: same 4-col layout
- Panel max-width: none (fills container)
- At <768px: grids collapse to 2 columns (already in responsive block L204–233 of app.css)
- No `overflow-x` on the panel itself; content wraps via grid

## Files Touched

| File | Role |
|------|------|
| `ui/fleet_health.js` | Composite score + per-host card rendering |
| `ui/fleet_status.js` | Compact status strip (ops panel) |
| `ui/fleet_topology.js` | SVG topology diagram (separate section) |
| `ui/app.css` L120–137, L244+ | Fleet panel layout + topology styles |
| `ui/tokens.css` | Color tokens used above |

## Acceptance Checklist

- [x] Spec doc exists (this file)
- [ ] Implementation matches spec: host cards with VRAM gradient bars
- [ ] Agent cards render with status dots + goal titles
- [ ] All 4 hosts + 8 agents visible at 1200px without overflow
- [ ] Sparklines present with native `<title>` tooltips
- [ ] Animations respect `prefers-reduced-motion`
