# Goal 1: Design Token Audit & Gap Closure — RE-LAND (2026-11-17 pass)

## Problem
Previous fix was reverted by mirror cycle. 36 hard-coded hex colors detected outside :root.

## Actions
1. Mapped 3 values to existing tokens: #2a3342→var(--line), #3ddc84→var(--ok), #ff6b6b→var(--err)
2. Defined 23 new CSS custom properties in :root for all remaining unique colors
3. Replaced all 36 occurrences with var() references
4. Fixed circular reference bug (--line:var(--line) → --line:#2a3342)

## Verification
- grep hex outside :root: **0 hits** [PASS]
- Brace balance: 242/242 [PASS]
- File size: 23.6 KB

## New tokens added (23)
--card-sel-bg, --seg-on, --white, --msg-you-bg, --msg-you-border,
--dm-border, --dm-accent, --busy-text, --link, --link-hover,
--peek-bg, --peek-border, --peek-text, --peek-body,
--dot-idle, --dot-busy, --dot-err,
--queue-bg, --queue-text, --spin-track, --spin-active, --queue-item,
--banner-warn-border, --banner-warn-bg, --banner-warn-text

## Artifact
ui/app.css (edited in place)