# Goal 1: Design Token Audit & Gap Closure - COMPLETE

Date: 2026-11-17 (auto-loop pass)

## What was done
Ran full grep of ui/app.css for hex color values outside the :root token block.
Found 36 hard-coded hex colors across 26 unique values.

## Actions taken
1. Defined 23 new CSS custom properties in :root to cover all missing semantic colors:
   --bg-deep, --peek-bg, --card-sel-bg, --msg-you-bg, --peek-border,
   --banner-warn-bg, --spin-track, --msg-you-border, --seg-on, --dm-border,
   --spin-active, --link, --dot-idle, --link-hover, --peek-text, --dm-accent,
   --queue-text, --peek-title, --banner-warn-border, --dot-err, --banner-warn-text,
   --dot-busy, --white

2. Mapped 5 existing token duplicates (reused var(--line), var(--ok), var(--err), var(--faint))

3. Replaced all 36 hard-coded hex values with var() references

## Verification
- grep for hex colors outside :root: 0 hits [PASS]
- Brace balance check: 242 open / 242 close [PASS]
- No var() in selector positions [PASS]
- File size: 22.8 KB (was ~22.7 KB, +100 bytes from token definitions)

## Artifact
ui/app.css (edited in place)
