# Designer Goal #8 — Error & Empty State Design System (progress 2026-11-18)

## What was done this pass
Implemented the four `.state-*` CSS classes in `ui/app.css` (appended after line 268):

| Class | Purpose | Key tokens used |
|-------|---------|----------------|
| `.state-loading` | spinner + label, async fetch | --acc, --line, --sp-*, --fs-13, --dim |
| `.state-error` | icon + message + retry hint | --err, --faint, --sp-*, --fs-* |
| `.state-empty` | icon + "no items" label | --faint, --sp-*, --fs-* |
| `.state-conn-lost` | full-width banner with pulsing dot | --warn, --panel2, --line, --sp-*, --fs-12 |

Spinner reuses existing `@keyframes qspin`; connection dot reuses existing `@keyframes pulse`.
No new keyframes added. All colors/spacing from token layer (zero hard-coded values in new block).

## Acceptance criteria status
- [x] 4 states defined and implemented in CSS
- [x] Uses token layer for all colors/sizes
- [x] Documented in components.md (section 7, pre-existing)
- [ ] Used in at least 2 panels as proof — NEXT STEP: wire into core.js or a panel

## File changed
- ui/app.css (+10 lines, now 279 total)
