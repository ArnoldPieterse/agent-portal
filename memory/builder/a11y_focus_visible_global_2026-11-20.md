# A11y Goal #7 — Global :focus-visible rule (increment 2)
Date: 2026-11-20
Agent: Builder

## What was done
Added a global `:focus-visible` CSS rule in `ui/app.css` (after the existing scoped ops-panel rule) that covers ALL interactive elements portal-wide:

```css
button:focus-visible, a:focus-visible, input:focus-visible,
select:focus-visible, [tabindex]:focus-visible {
  outline: 2px solid var(--focus); outline-offset: 2px;
}
```

This ensures keyboard users get a visible focus indicator on every button, link, input, select, and any `tabindex`-bearing element — not just those in the ops panel and mode bar.

## Verification
- `ui/app.css` brace balance: 324/324 ✓
- Rule uses `--focus` token (dark: #7fb0ff, light: #2767d8) — both pass contrast on their respective backgrounds
- `:focus-visible` is supported in all modern browsers (Chrome 86+, Firefox 85+, Safari 15.4+); fallback: no visual change for mouse users (correct behaviour)

## Remaining for full closure of goal #7
- Live tab-through test (requires browser session)
- Screen reader announcement test (requires browser + SR like NVDA/VoiceOver)
- `aria-live` on dynamic regions (chat panel, fleet status strip) — can be done without browser but deferred to next increment

## Increment 2b: aria-live on dynamic regions
Added `aria-live="polite"` to `#msgs` (chat message list) and `#fleetStat` (fleet status) via JS in `ui/core.js` (line 7, runs before any rendering). Set via `setAttribute` because index.html is pinned — avoids the clobber loop.

- `ui/core.js` brace/paren balance: 313/313 / 1130/1130 ✓
- `#opsMsg` already had `aria-live="polite"` in markup (line 69)

## Files touched
- `ui/app.css` (+4 lines: global focus-visible rule)
- `ui/core.js` (+2 lines: aria-live on #msgs and #fleetStat)