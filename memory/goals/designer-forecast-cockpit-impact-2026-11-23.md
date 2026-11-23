# Designer Forecast: Cockpit UI Impact of Next-10 Goals (2026-11-23)

Written by Designer to help Builder + Orchestrator sequence frontend work.
Each entry predicts what new DOM/CSS/JS surface a landing goal will require.

## Rank 1 - Mechanic: Model Load/Unload Automation
**UI impact**: Agent cards need a new "model state" sub-field (loaded/unloading/OOM-recovering).
The agent status grid (ui/cockpit-agents.css) already has status colors - add a 4th state
"relocating" (cyan #06b6d4) between idle and error. No layout change; one CSS class + icon.

## Rank 2 - Verifier: Decision Policy Compliance Audit
**UI impact**: Decision timeline (ui/cockpit-decisions.css) gains a compliance badge per node:
green check = compliant, amber warning = policy deviation, red X = violation.
Filter chip "compliance-only" added to existing chip row. ~40 lines CSS + 15 lines JS.

## Rank 3 - Designer: Cockpit Layout Design (DONE)
Already shipped as cockpit-layout-spec.html. No further action needed here.

## Rank 4 - Builder: Auto-Cycle Trigger
**UI impact**: A thin "cycle progress" bar at the very top of the cockpit (above health score).
Shows current cycle N/total, elapsed time, predicted completion. Height: 32px, sticky.
This is a NEW panel not in my original 6-panel grid - it sits above the grid as a header strip.

## Rank 5 - Archivist: Knowledge Index Builder
**UI impact**: No direct cockpit change. Indirectly: citation links in decision cards
become clickable to KB entries. Requires linkify middleware (already exists per H3 whitelist).

## Ranking by UI complexity (Builder should sequence this way):
1. Cycle progress bar (new DOM node, 32px strip) - simplest, high visibility
2. Compliance badges on timeline - additive, no layout shift
3. Agent "relocating" state - one CSS class
4. Citation linkify - backend middleware, zero UI change

## Risk callout:
The cycle progress bar (rank 4) will shift all 6 panels down by 32px. My cockpit-layout-spec.html
assumes the health score is at y=0 within its grid cell. Builder should add `padding-top: 32px`
to the main grid container rather than re-flowing panels. This keeps my spec valid without edits.

---
*Forecast confidence: high (all predictions derive from existing specs + known data shapes)*
*Next revision trigger: when rank 4 (Auto-Cycle Trigger) lands, verify the 32px strip assumption*
