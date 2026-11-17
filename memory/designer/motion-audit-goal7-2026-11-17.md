# Goal 7 - Motion & Animation Audit (2026-11-17)

## Findings

### Transitions (all interactive elements)
| Element | Properties | Duration | Budget | Pass |
|---------|-----------|----------|--------|------|
| #modeBar button, .seg button, .btn, #send | border-color, color, background-color, opacity | 150ms | <=200ms | Y |
| .dot | background-color | 200ms | <=200ms | Y |
| .flink | color, border-bottom-color | 150ms | <=200ms | Y |
| .ft-host rect | stroke, fill | 150ms | <=200ms | Y |

**Result: All interactive transitions within 200ms budget. Zero violations.**

### Infinite-loop animations (non-essential)
| Class | Animation | Cycle | Purpose | Reduced-motion handling |
|-------|-----------|-------|---------|------------------------|
| .busyspan | pulse | 1.3s ease-in-out inf | Busy status text fade | Disabled -> static opacity .7 |
| .qspin | qspin | 0.9s linear inf | Queue spinner rotation | Disabled -> static dashed border |

### Fix applied
Added `@media(prefers-reduced-motion:reduce)` block at end of `ui/app.css`:
- Kills all animations/transitions globally (duration -> .01ms, iteration -> 1)
- `.busyspan` gets explicit `animation:none; opacity:.7` (visible but static)
- `.qspin` gets explicit `animation:none; border-style:dashed` (visible as static indicator)

## Verification
- grep confirms zero transition/animation duration >200ms on interactive elements
- `prefers-reduced-motion` block present in app.css
- No JS-driven animations found (only one setTimeout(400ms) in core.js for debounce, not animation)

## Files changed
- ui/app.css (+11 lines: reduced-motion media query)
