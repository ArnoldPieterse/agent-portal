# Live Design Asset Map — where the canonical UI lives in `ui/`

Quick-lookup for any agent building new UI. This points at the **live** files (not
evidence leaves). Verified accurate 2026-11-21 by grep against disk.
Parent index: memory/designer/INDEX.md

## Start here — one file per concern
| Concern | Live file | What to use |
|---|---|---|
| Design tokens + themes | `ui/tokens.css` (~4 KB) | 79 CSS custom props. Dark = `:root` default; light = `[data-theme=light]`; high-contrast = `[data-theme=high-contrast]` (AAA). Also a `prefers-color-scheme: light` fallback block. |
| Icon set | `ui/icons.js` (~10 KB) | 28 inline SVGs, all `currentColor`, no external font deps. Required min 10 present: agent, host, model, alert, check, error, loading, search, settings, close. Others incl. goal/upload/wrench/robot/menu/refresh/folder/satellite. |
| Components | `ui/components.js` (~18 KB) | `card, badge, gauge, timelineNode, collapsiblePanel, toast, skeleton, emptyState, progressBar, tooltip, errorState` (+ helpers `esc`, `el`). Per-function docs: memory/designer/component-reference.md |
| Motion | `ui/animations.css` (~3 KB) | @keyframes: panel-enter, li-enter, gauge-fill, ring-fill, notif-slide-in. All compositor-friendly (transform/opacity/stroke-dashoffset); `prefers-reduced-motion` guard present. |
| Layout + responsive | `ui/app.css` (~37 KB) | Markup-only shell is index.html; all UI styles here. Breakpoints at **375px** and **768px** (4 @media blocks). No horizontal scroll on main panels; touch targets >=44px. |
| Error/empty/loading states | `ui/core.js` + components.js | `UI.errorState()` wired into fleet, activity, merge-queue panels. Never emit raw "Error" text without context — use emptyState/skeleton/errorState/toast. |
| Performance budget | `ui/core.js` | `window.__perf` (initEnd/interact/frameBudget) + 2× `performance.mark`; debug-gated behind `?debug`. Budgets: init <2s, interaction <100ms, frame 16ms. Spec: memory/designer/css-bundle-budget-2026-11-17.md |
| Theme switching | `ui/core.js` (IIFE) | Cycles dark/light/high-contrast; persists to localStorage. Set `data-theme` on `<html>`/root — never hardcode colors outside `var()`. |

## A11y tooling (run these before shipping UI)
- `memory/designer/a11y_tree_verify.py` — heading order + landmarks (nav/main/aside) on index.html.
- `memory/designer/aria_audit.py` — flags controls missing accessible names (currently 0/49).
- `memory/designer/contrast_audit.py` — WCAG contrast vs live token values.

## Rules of the road for new UI
1. Consume tokens via `var(--…)` only; add new tokens to `ui/tokens.css`, not inline.
2. Use an icon from `ui/icons.js`; do not reintroduce emoji or text glyphs for status.
3. Reuse a component before writing markup; if missing, add it to `ui/components.js` + document in component-reference.md.
4. Respect the 768px/375px breakpoints and >=44px touch targets.
5. Honor `prefers-reduced-motion`; keep animations <400ms and compositor-only.
