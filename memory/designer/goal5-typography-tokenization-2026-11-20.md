# Goal #5 Typography Scale Refinement - PROGRESS (2026-11-20)

One concrete step this pass: tokenized the font stacks + eliminated every off-scale font-size literal.

## What changed (files in shared agent folder, relative paths)
- `ui/tokens.css` - added two tokens to :root:
  - `--font-sans:system-ui,Segoe UI,Roboto,sans-serif;`
  - `--font-mono:ui-monospace,Consolas,monospace;`
- `ui/app.css` - replaced all hardcoded stacks with the tokens (8 replacements):
  - 5x `font-family:ui-monospace,Consolas,monospace` -> `var(--font-mono)` (lines ~106 peek .pk-body, 123 .fmodels, 129 .opsbox, 134 #actBody, 258 .ft-dt-base)
  - 3x `font-family:system-ui,Segoe UI,Roboto,sans-serif` -> `var(--font-sans)` (body x2, .ft-wrap)
- `ui/fleet_goals_bars.js` - 2 SVG `<text>` elements had literal `font-size="12"` (off-token); now `style="font-size:var(--fs-12)"`.

## Measurement (re-ran audit after edits)
- font-size declarations across app.css/interactions.css/animations.css: **101**
- off-scale literals: **0** (every value is var(--fs-*))
- leftover hardcoded font stacks in CSS: **0**
- tokens present: --font-mono True, --font-sans True

## Acceptance criteria status
- [x] all font-size values in CSS from the defined scale (measured: 0 off-scale)
- [x] no orphaned / stray sizes (all on --fs-* tokens; monospace now tokenized too)
- [x] monospace for code/paths consistent + tokenized (--font-mono)
- [~] line-length <75ch: controlled by existing max-width (msg 78%, thinkwrap 62%) + word-break/overflow-wrap; no explicit ch cap yet
- [ ] final visual check (readability / no layout shift) - manual, next pass

STATUS: progress. Core quantitative criteria met & measured; not marked fully verified yet pending a visual pass.
