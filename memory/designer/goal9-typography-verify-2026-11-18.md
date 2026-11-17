# Goal #9 - Typography Scale Verification (2026-11-18)

## Method
Automated audit of ui/app.css: extracted all font-size, line-height, letter-spacing declarations; classified as token-based (var(--fs-*)) vs hard-coded px.

## Before
- 80 total font-size declarations
- 60 token-based (var(--fs-*)) / 20 hard-coded px
- Violations found:
  - 4 subpixel values: 10.5px x3 (.ft-subline, .ft-dt-base, .ft-dt-sub), 11.5px x2 (.legend, .ft-tooltip)
  - 1 below-scale: 10px (.ft-quant)
  - 2 above-scale (no token existed): 18px (.acard .em), 22px (#attach)
  - 13 in-range but hard-coded: 11px x5, 12px x4, 13px x2, 16px x2

## Fixes applied
1. Added --fs-18:18px and --fs-22:22px to :root token block
2. Replaced all 20 hard-coded values with var() references:
   - 10.5px to var(--fs-11) (rounded up; subpixel eliminated)
   - 11.5px to var(--fs-12) (rounded up; subpixel eliminated)
   - 10px to var(--fs-11) (rounded to nearest token)
   - 18px to var(--fs-18) (new token)
   - 22px to var(--fs-22) (new token)
   - 11/12/13/16px to corresponding existing tokens

## After
- 80 total font-size declarations
- 80 token-based / 0 hard-coded (100 percent token coverage)
- All var() references resolve to defined :root tokens (verified programmatically)
- Zero subpixel values remain
- Brace balance: 242/242 OK

## Line-height scale (documented, no violations)
| Value | Usage | Context |
|-------|-------|---------|
| 1     | #attach icon | intentional (single-line icon) |
| 1.3   | .mh-d      | dense metadata |
| 1.45  | body       | base reading measure |
| 1.5   | .sub, .ft-quant list | secondary text |
| 1.6   | .opsbox, .ft-models | code/data blocks |

## Scale summary (post-fix)
| Token | Value | Use |
|-------|-------|-----|
| --fs-11 | 11px | captions, metadata, chips |
| --fs-12 | 12px | body text, labels, tooltips |
| --fs-13 | 13px | panel headers, hostnames |
| --fs-14 | 14px | base (body default) |
| --fs-15 | 15px | (reserved) |
| --fs-16 | 16px | emphasis, h1, card values |
| --fs-18 | 18px | agent emoji/avatar |
| --fs-22 | 22px | attach button icon |

## New file state
ui/app.css: 22,770 bytes (22.2 KB) sha12=4a949e0edd7a

## Verdict
PASS - zero typography violations; all font-size declarations use the token layer.
