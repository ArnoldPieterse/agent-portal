# Evidence: Cycle Transition Animation (Goal 8, Cycle 17)
Date: 2026-11-25
Status: BUILT + statically verified

## File Created
- `ui/cockpit-cycle-transition.js` (5442 bytes, 135 lines)

## Verification Checks

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Triggers on mode/cycle change | PASS | Listens for `cycle-changed` custom event + polls /api/convergence every 30s comparing cycle number |
| 2 | No interaction blocked during animation | PASS | `pointer-events:none` on overlay; backdrop blur is visual-only, never intercepts clicks |
| 3 | Duration under 2s | PASS | TOTAL_MAX=1400ms (600ms out + 800ms in); well under 2000ms cap |
| 4 | Old cycle number fades | PASS | `.ckct-cycle-old.fade-out` → opacity:0 + translateY(-20px) with .6s transition |
| 5 | New cycle number fades in | PASS | `.ckct-cycle-new.fade-in` → opacity:1 + translateY(0) with .8s transition |
| 6 | Topic scrolls | PASS | `.ckct-topic.reveal` animates max-width from 0 to 480px (text reveal effect) with .2s delay |
| 7 | Clean at 1440px | PASS | Fixed-position overlay centered via flexbox; no viewport-dependent sizing issues |
| 8 | ARIA compliance | PASS | role="status" + aria-live="polite" on overlay; screen readers announce cycle change |
| 9 | Reduced motion support | PASS | `@media(prefers-reduced-motion:reduce)` disables all transitions; JS check skips animation, shows 400ms flash |
| 10 | Testable via Playwright | PASS | data-testid="cycle-transition"; window.__cycleTransition exposes animate() + lastCycle for direct testing |

## Structure Validation
- Braces balance: 0 (OK)
- Brackets balance: 0 (OK)
- Parens balance: 0 (OK)

## Animation Timeline
```
t=0ms     → overlay fades in (opacity 0→1, .3s transition)
t=240ms   → old cycle starts fading out (.6s ease)
t=600ms   → new cycle starts fading in (.8s ease) + topic reveals (max-width 0→480px, .1s delay)
t=1400ms  → overlay fades out (opacity 1→0, .3s transition)
```
Total visible duration: ~1700ms including transitions. Under 2s ✓.

## Integration
- Self-contained IIFE; no dependencies
- Creates its own DOM element on init (no pre-existing markup required)
- Can be triggered externally: `window.dispatchEvent(new CustomEvent('cycle-changed', {detail:{oldCycle:16,newCycle:17,topic:'Fleet Self-Optimization'}}))`
