# Goal 9: Typography Scale Verification - PASS
Date: 2026-11-18 | sha12(app.css)=1d7a72e3ab19

## Changes made
1. Added --fs-10:10px token to :root (for SVG micro-labels in fleet topology)
2. .mh-v font-size 16px -> var(--fs-16)
3. h1 font-size 16px -> var(--fs-16)
4. .legend font-size 11.5px -> var(--fs-12) (rounded up for readability)
5. Tooltip content font-size 11.5px -> var(--fs-12)
6. .ft-subline font-size 10.5px -> var(--fs-10) (SVG label)
7. .ft-dt-base font-size 10.5px -> var(--fs-11) (monospace readability)
8. .ft-dt-sub font-size 10.5px -> var(--fs-11) (uppercase label)
9. .ft-quant font-size 10px -> var(--fs-10)

## Verification results
- Font-size scale: all values within 10-16px range (70 token refs + 2 intentional exceptions)
- Line-heights: all within 1.0-1.7 ([1.0, 1.3, 1.45, 1.5, 1.6, 1.7])
- Letter-spacing: 3 rules, all on uppercase label elements only
- Font-weights: 4 distinct steps (400/600/650/700)
- No fractional pixel sizes remain

## Scale reference (post-fix)
| Token | Value | Usage |
|-------|-------|-------|
| --fs-10 | 10px | SVG micro-labels, tiny accents |
| --fs-11 | 11px | captions, metadata, fleet detail |
| --fs-12 | 12px | body text (default) |
| --fs-13 | 13px | emphasis, panel titles |
| --fs-14 | 14px | headings |
| --fs-15 | 15px | sub-headings |
| --fs-16 | 16px | h1, prominent values |

Intentional exceptions (not text): .acard .em=18px (emoji), #attach=22px (icon glyph in 44px button)
