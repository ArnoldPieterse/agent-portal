# Designer goals #2/#3/#6/#7 - patched file ready (2026-11-16)

## Artifact
`designer/index-patched-v2.html` - sha12 `3464076efc48`, 1278 lines.
Based on live pin df1bbdaef684 with all changes applied and verified.

## Changes applied (all additive, zero removed functionality)

### Goal #3: WCAG AA contrast fix
- Added `--acc-deep:#2563eb` to :root
- `.btn.pri` now uses `background:var(--acc-deep)` - white text contrast 5.17:1 (was 3.22:1 on #4f8cff)
- Only ONE pair was failing; all others verified >= 4.5:1

### Goal #2: Ops panel visual hierarchy
- Added `.ops-label` class (uppercase, letter-spaced, border-bottom divider) for section headers
- Replaced 3 inline-style labels with semantic `.ops-label` elements: Git status / Recent commits / Host tiles
- Added "Actions" label + wrapped commit input and buttons in `.ops-actions` container (bg, border, padding)
- Commit button promoted to `.btn pri` (primary action = most prominent)
- Prune button styled as `.btn danger` (warning-color border = destructive action signaling)

### Goal #6: Micro-interactions
- Added `:active` state for all buttons and cards: `opacity:.78; transform:scale(.98)` at 50ms
- Added hover transform on agent cards: `translateX(2px)` with 150ms transition
- All transitions <= 200ms, zero layout shift (transform only)

### Goal #7: Responsive breakpoints
- `@media(max-width:768px)`: sidebar collapses to 56px icon rail, ops panel height capped, rows wrap
- `@media(max-width:375px)`: sidebar hidden, font drops to 13px, messages full-width, actions stack vertically

## Verification checklist (for post-apply)
- [ ] Hard refresh :8099 - no console errors
- [ ] Ops panel shows 4 labeled sections with visual hierarchy (labels > content > actions)
- [ ] Commit button is blue-filled (primary), Prune has orange border (danger)
- [ ] Click any button - brief press feedback (opacity dip + slight shrink)
- [ ] Resize to 768px - sidebar narrows, no horizontal scroll
- [ ] Resize to 375px - sidebar hidden, all content fits single column

## Apply method
Copy `designer/index-patched-v2.html` over the shared-root `index.html`.
Single file replacement - no script needed. Verify sha12 after copy = `3464076efc48`.
