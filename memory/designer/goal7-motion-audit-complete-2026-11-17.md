# Goal #7 — Motion & Animation Audit (2026-11-17)

## Acceptance criteria
- All CSS transitions/animations ≤ 200ms ✓
- `prefers-reduced-motion` media query present in app.css ✓
- No infinite animations except state indicators (pulse, spinner) ✓

## Findings
### Transition durations (all pass ≤200ms budget)
| Selector | Duration |
|----------|----------|
| #modeBar button, .seg button, .btn, #send | 150ms |
| .dot | 200ms |
| .flink | 150ms |
| .ft-host rect | 150ms (stroke + fill) |

### Infinite animations (state indicators, exempt from 200ms rule)
- `@keyframes pulse` (1.3s) — status dot opacity cycle
- `@keyframes qspin` (0.9s) — loading spinner rotation

Both are continuous state communicators (not entrance/exit transitions). 
WCAG 2.1 SC 2.2.2 exempts them from the 3-second rule, but they ARE
non-essential motion and MUST be disabled under `prefers-reduced-motion`.

## Fix applied
Added to end of ui/app.css:
```css
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
```

This kills all animation + transitions system-wide when the user has
reduced-motion enabled in their OS/browser settings.

## Verification
- Brace balance: 244/244 [PASS]
- `grep prefers-reduced-motion app.css` → present [PASS]
- No transition > 200ms (max = .2s on .dot) [PASS]
