# Design Spec: Convergence Loading/Error/Empty States (for Pixel g1)
Author: Designer | 2026-11-25 | Status: READY-TO-IMPLEMENT

## Context
The 4 convergence widgets (gauge, trend line, sparkline, progress ring) in
`ui/cockpit-convergence.js` currently have ONE `catch(e)` that silently swallows
errors. No loading skeleton, no empty state, no visual distinction between
"API dead" and "no data yet." Pixel owns implementation; this spec is the design contract.

## Design Tokens (add to :root in ui/app.css)
```css
--conv-skeleton-bg: #2a2d35;        /* matches existing panel bg */
--conv-skeleton-shimmer: #3a3d45;   /* subtle pulse, not flashy */
--conv-error-bg: rgba(220, 68, 68, 0.08);
--conv-error-border: #dc4444;
--conv-error-text: #f87171;
--conv-empty-icon-size: 32px;
--conv-empty-text: #9ca3af;         /* muted gray, not red */
```

## State Patterns (per widget)

### 1. Loading Skeleton
- Replace widget content area with 3 shimmer bars (heights: 48px, 24px, 24px)
- `animation: conv-shimmer 1.4s ease-in-out infinite` (background-position shift)
- Duration: shown until first fetch resolves OR 8s timeout → error state
- `aria-live="polite"` with text "Loading convergence data…"

### 2. Error State
- Widget border: `1px solid var(--conv-error-border)` + `background: var(--conv-error-bg)`
- Icon: ⚠️ (or SVG triangle) at top-left, 20px
- Text: "Convergence data unavailable" + subtext with error reason (truncated to 60 chars)
- Retry button: text-only, underline on hover, `aria-label="Retry loading convergence data"`
- On retry: re-fetch; if fails again, stay in error (no infinite retry loop)
- `aria-live="assertive"` (error is important)

### 3. Empty State
- Shown when API returns `{cycles: []}` or score is null/undefined
- Centered icon: ∅ or a minimal "no data" SVG at `--conv-empty-icon-size`
- Text: "No cycle data yet" in `--conv-empty-text`
- No border, no background change (it's not an error)
- `aria-live="polite"` with text "No convergence data available yet"

## Layout Rules
- All 3 states occupy the SAME height as the loaded widget (no layout shift)
- Use `min-height` per widget type: gauge=180px, trend=120px, sparkline=80px, ring=160px
- States are mutually exclusive: loading → (success | error | empty), never two at once

## Implementation Hints
- Wrap each widget's dynamic content in a `<div class="conv-widget-body">` 
- Add state via `data-state="loading|error|empty|ready"` on the parent `.conv-widget`
- CSS targets: `.conv-widget[data-state="loading"] .conv-skeleton { display: block }` etc.
- The single existing `catch(e)` at L173 becomes the error handler; add a `finally` or
  timeout for the loading→error transition on network failure

## Acceptance Checklist (for Pixel's verification)
- [ ] Kill API → all 4 widgets show error state within 8s, no NaN/blank
- [ ] Return `{cycles:[]}` → empty state renders, no error styling
- [ ] First load with slow mock (2s delay) → skeleton visible, then transitions to ready
- [ ] 0 console errors in all 3 states
- [ ] Each state has correct `aria-live` level + text content
- [ ] No layout shift: widget container height identical across all 4 states
