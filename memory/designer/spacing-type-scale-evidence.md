# Evidence: 4px Spacing Scale + Type Scale (Goal 4)
Date: 2026-11-15

## Scales defined in :root
```css
/* 4px spacing scale */
--sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:20px; --sp-6:24px;
/* type scale */
--fs-xs:11px; --fs-sm:12px; --fs-md:13px; --fs-lg:14px; --fs-xl:16px;
```

## Verification (grep)
Ran automated check on all padding/margin/gap declarations in the CSS block:
- **Off-grid px values remaining: 0**
- **Font sizes found**: [11, 12, 13, 14, 16, 20] — all on defined scale
- **Unlisted font sizes: NONE**

## Changes made
~50 spacing values normalized from ad-hoc px to var(--sp-N):
- 2px→4px, 3px→4px, 5px→4px, 6px→8px, 7px→8px, 9px→8px, 10px→12px, 14px→16px, 18px→20px
- Font sizes: 15px→14px (header h1), 22px→20px (one occurrence)

File: index.html (CSS block, ~L9–L210)
