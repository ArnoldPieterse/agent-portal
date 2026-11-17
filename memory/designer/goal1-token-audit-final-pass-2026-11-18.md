# Goal 1: Design Token Audit — Final Pass (2026-11-18)

**Status: COMPLETE**

## What was done
Added 25 color tokens + 3 radius tokens + 2 duration tokens + 1 font-size token to `:root` in `ui/app.css`. Replaced all hardcoded hex colors, border-radius values, and transition durations with `var(--token)` references.

## Tokens added
**Colors (25):** --bg-alt, --panel3, --card-sel-bg, --msg-you-bg, --line-alt, --warn-bg, --spin-track, --msg-you-border, --btn-active, --dm-border, --link-hover, --acc-bright, --gray-mid, --dim2, --gray-dim, --focus-bright, --text-muted, --dm-text, --text-light, --text-bright, --warn-alt, --err-alt, --gold, --orange, --white

**Radii (3):** --radius-sm:4px, --radius-md:8px, --radius-lg:12px

**Durations (2):** --dur-fast:150ms, --dur-med:200ms

**Font-size (1):** --fs-18:18px

## Verification
- `grep` for hex colors in app.css outside :root: **0 hits** (only false positives are CSS ID selectors like #addAgent)
- 31 radius token usages, 6 duration token usages in the file
- File size: 23.4 KB (was 22.6 KB before; +0.8 KB for token definitions)
- Note: `animation:pulse 1.3s` on `.busyspan` is an infinite loading pulse, not a transition — exempt from the 200ms budget (see goal #7)

## Acceptance test result
**PASS**: zero hard-coded hex colors remain in ui/app.css outside the :root block.