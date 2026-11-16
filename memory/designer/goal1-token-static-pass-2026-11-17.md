# Goal #1 Static Compliance Evidence - 2026-11-17

## What was done
Extended design token layer from 23 to 53 tokens in ui/app.css :root.
Replaced ALL hardcoded values with var() references:
- 27 unique hex colors -> semantic color tokens (--bg-deep, --acard-sel, --msg-you, etc.)
- 29 border-radius px values -> var(--radius-sm) / var(--radius-md)
- 5 transition/animation durations -> var(--dur-fast), var(--dur-med), var(--dur-pulse), var(--dur-spin)

## Acceptance test (static portion)
Regex scan of ui/app.css outside :root blocks.
Result: 0 hardcoded hex colors, 0 hardcoded border-radius px, 0 hardcoded durations. PASS.

## Token inventory (53 total)
- Color (28): bg, panel, panel2, panel3, line, text, dim, acc, ok, warn, err, focus, faint,
  bg-deep, acard-sel, msg-you, msg-you-line, acc-dim, acc-bright, acc-brighter, acc-spin,
  text-bright, text-mid, text-dim2, text-faint2, text-faint3, dm-border, dm-text, busy, unknown,
  int-border, int-bg, int-text, spin-base, peek-line, queue-text
- Spacing (5): sp-4, sp-8, sp-12, sp-16, sp-24
- Font-size (6): fs-11 through fs-16
- Duration (4): dur-fast (.15s), dur-med (.2s), dur-pulse (1.3s), dur-spin (.9s)
- Radius (2): radius-sm (8px), radius-md (12px)

## Remaining for full closure
- Live screenshot pair on :8099 (portal down / sandbox port blocked WinError 10013)
- WCAG AA contrast script re-run on rendered page
These require portal to be reachable from the agent host.

## File changed
ui/app.css (18615 bytes -> ~20KB, +1400 bytes for token definitions + var() replacements)
