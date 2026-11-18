# Goal #7 Typography Hierarchy Audit - Evidence (2026-11-19)

## What was done
Static source-code audit across all `ui/*.css` + `ui/*.js` files. Found and fixed 45 off-scale font-size violations.

## Scale enforced
h1=24px, h2=18px, h3=15px, body=14px, caption=12px (5-step scale)

## Changes made
1. **tokens.css**: Added `--fs-18:18px` and `--fs-24:24px` tokens.
2. **app.css** (15 + 30 = 45 replacements):
   - h1: 16px → var(--fs-24)
   - Fleet SVG labels (.ft-*): 10/10.5/11/11.5/13px → var(--fs-12) or var(--fs-14)
   - Header values (.mh-*): 11/16px → var(--fs-12)/var(--fs-15)
   - Chat UI (chips, hints, buttons): --fs-11→--fs-12, --fs-13→--fs-14, --fs-16→--fs-15
   - Attach button: 22px → var(--fs-18)
   - Code inline: 11px → var(--fs-12)
3. **core.js**: 4 inline font-size fixes (10px/11px → 12px)
4. **uploads.js**: 3 inline font-size fixes (10px → 12px)
5. **components.js**: 3 inline font-size fixes (9px/10px → 12px)

## Verification
Python script audit: 0 off-scale values remaining across all UI files.
Total declarations checked: 94 (80 CSS + 14 JS).
All conform to {12, 14, 15, 18, 24}px.
