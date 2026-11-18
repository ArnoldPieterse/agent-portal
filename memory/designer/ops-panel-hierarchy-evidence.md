# Evidence: Ops Panel Hierarchy Redesign (Goal 2)
Date: 2026-11-15

## Before
All elements in #opsBody shared identical `.opsbox` class (12px mono, var(--dim), same border/padding).
Git status, git log, host tiles, and the action row (commit input + buttons) had no visual weight difference.
Labels were inline `<div>` with `font-size:12px;color:var(--dim)` — same as content.

## After (structural changes in index.html)
Three-tier hierarchy introduced:
1. **Tier 1 — Display (recessed)**: `.ops-label` (11px, uppercase, --faint) above each `.opsbox`. Read-only zone.
2. **Tier 2 — Host tiles (neutral)**: `.ops-tiles` flex row with equal-width tiles.
3. **Tier 3 — Actions (elevated)**: `.ops-actions` container with `background:var(--panel2)` (lighter than --panel), own border+radius, containing:
   - Primary action: `.btn-primary` (accent bg, dark text, bold) for Commit
   - Secondary action: `.btn-secondary` (ghost/outline) for Prune

Key CSS tokens added:
- `.ops-label`: 11px uppercase --faint — distinguishes section headers from content
- `.ops-actions`: elevated bg + border separates action zone from display zone  
- `.btn-primary` / `.btn-secondary`: clear primary vs secondary button hierarchy
- `#opsBody` now uses flex column with 12px gap between tiers

File: index.html (lines ~129–149 CSS, lines ~233–260 HTML)
