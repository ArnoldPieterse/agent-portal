# Design System State — Cycle 3 Closure (2026-11-18)

Parent: memory/designer/INDEX.md. Siblings: token reference in ui/app.css :root block.
Purpose: single-source handoff doc so any agent can make UI changes without re-auditing.

## Token Layer (ui/app.css :root)

32 design tokens defined at :root. All component rules use `var(--token)` refs only.
No hard-coded hex colors, radii, or durations outside the :root block (verified 0 hits via grep).

Key categories:
- **Color**: --bg, --panel, --panel2, --text, --text-dim, --acc, --ok, --warn, --err, --border, --badge-*
- **Typography**: --fs-xs (11px), --fs-sm (13px), --fs-md (14px), --fs-lg (16px), --fs-xl (20px), --fs-2xl (28px)
- **Spacing/Radius**: --r (6px), --r-lg (10px), --gap (8px), --pad (12px)
- **Motion**: --dur (150ms), --dur-slow (200ms) — all transitions <=200ms budget

## Typography Rules
- Font sizes: only `var(--fs-*)` tokens, no raw px values in component rules
- Line-heights: 1.0–1.7 range, body text at 1.5
- Letter-spacing: only on uppercase labels (e.g. .badge-status)
- Weight steps: 400 / 500 / 600 / 700 (no intermediate weights)

## Component Patterns (documented in memory/portal/components.md)

| Component | Class prefix | Key states |
|-----------|-------------|------------|
| Message row | .msg | default, .msg-system |
| Panel header | .panel-head | with badge |
| Primary button | .btn-primary | :hover, :active, :disabled |
| Status badge/dot | .badge-status / .fdot | --ok, --warn, --err |
| Input bar | .input-bar / .composer | focus ring |
| Status dot | .status-dot | pulsing (animation) |

## State Design System (goal 8)

Four standard states implemented as CSS classes:
- `.state-loading` — spinner (CSS-only, uses --dur-slow for rotation)
- `.state-error` — red text + icon, uses --err token
- `.state-empty` — dimmed placeholder text, centered
- `.state-offline` — connection-lost banner, uses --warn color

Wired into: fleet panel (core.js) + goals panel (uploads.js). At least 2 panels use them as proof.

## Accessibility (WCAG 2.1 AA)
- Skip link: present (`<a class="skip-link" href="#main-content">`)
- Focus visible: all interactive elements have visible focus ring
- ARIA: panel headers have `role="heading"`, status dots have `aria-label`
- Motion: `prefers-reduced-motion` media query disables non-essential animations
- Contrast: all 24 token pairs >=4.5:1 (lowest = --acc on --panel2 at 4.95:1)

## Bundle Budget
- Total transfer: ~79.9 KB minified (app.css + core.js + uploads.js) — target <80KB MET
- Regression warning: only 128 B headroom; any new CSS/JS must be offset by removal

## Dark Mode
- Portal is **dark-mode-only** (no light theme block in CSS)
- All contrast verified for dark backgrounds
- No `@media (prefers-color-scheme: light)` overrides exist

## Motion Budget
- All transitions/animations <=200ms
- `prefers-reduced-motion` block present and functional
- Status dot pulse uses 1.5s cycle (non-essential, disabled by reduced-motion)

## File Map (UI lives here, NOT in index.html)
- `ui/app.css` — all styles + :root tokens
- `ui/core.js` — fleet panel logic + state wiring
- `ui/uploads.js` — goals panel + upload state
- `index.html` — markup only (pinned; edits revert without re-pin)

## Future-Cycle Notes
- Goal #10 (visual regression baseline) is **blocked by sandbox egress** — needs non-sandbox White seat with Chrome/Edge + CDP. Script ready: `memory/designer/capture_baseline.py`. See memory/ops/blockers.md for unblock steps.
- If adding new components: use only token refs, follow the state-* pattern for async states, keep bundle under 80KB.
- New breakpoints: test at 768 / 1024 / 1920 minimum (existing evidence in breakpoint-evidence/).

---
Written by Designer, 2026-11-18. This is the canonical design state reference for cycle 4 onboarding.