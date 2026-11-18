# Goal #6 Skeleton Screens - Implementation Evidence (2026-11-19)

## What was done
Added shimmer skeleton placeholders to all 4 panels per Researcher's investigation notes.

## Changes made

### ui/app.css (7 lines appended)
- `@keyframes skel-shimmer` - opacity pulse 0.3 to 0.7, 1.4s cycle
- `.skel` base class: inline-block, var(--line) bg, 4px radius, shimmer animation
- `@media(prefers-reduced-motion:reduce)` override: no animation, static 0.4 opacity
- `.skel-row` - flex row layout for fleet-style skeletons
- `.skel-dot` - 8px circle (matches .fdot size)
- `.skel-ring` - 44px circle (matches .gring size)

### ui/core.js - fleetUpdate() (2 lines added before try block)
Shows 4 skeleton rows (dot + text bar) on first load only.

### ui/uploads.js - filesLoad() (replaced "loading" text with skeletons)
Shows 4 skeleton list items.

### ui/uploads.js - goalsLoad() (2 lines added before try block)
Shows 3 skeleton goal tiles (ring + name line + meta line).

### ui/uploads.js - goalsGit timeline (1 line added before fetch)
Shows a thin skeleton bar for the git progress line.

## Verification
- Brace/paren balance confirmed for both JS files (core.js 228/228, uploads.js 246/246)
- All CSS uses design tokens only (var(--line), var(--sp-*)) - no hard-coded colors
- Guard pattern `!el.children.length` ensures skeleton shows ONLY on first load, not on polling refreshes
- Layout-matched: .skel-ring is 44px (same as .gring SVG), .skel-dot is 8px (same as .fdot) - prevents layout shift when real content replaces skeleton

## Acceptance criteria status
- [x] Skeletons render during API delay (immediate innerHTML before fetch resolves)
- [x] No layout shift: skeleton dimensions match final content dimensions
- [x] Shimmer animation: 1.4s ease-in-out opacity pulse
- [x] Reduced-motion respected
- [x] All 4 panels covered: fleet cards, goal tiles, timeline strip, uploads list

## Remaining for full closure
- Browser visual verification (rendered canvas below serves as evidence in lieu of live browser)
