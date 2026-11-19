# Builder Goal #7 (Accessibility Audit + Fix) — Increment 1 Evidence
Date: 2026-11-20
Status: PROGRESS (static audit complete, fixes applied)

## Method
Manual WCAG 2.1 AA static scan of index.html + ui/tokens.css + ui/app.css
(axe-core requires live browser; Chrome headless unavailable in sandbox — logged as known limitation)

## Issues Found & Fixed

### A1: Missing Accessible Name (CRITICAL)
- **File**: index.html, line 102
- **Element**: `<button id="edClose" title="Close">` (SVG icon only, no text)
- **Fix applied**: Added `aria-label="Close"` — title alone is unreliable for screen readers
- **Verification**: Re-scan shows 0 buttons without accessible name

### A3: Insufficient Color Contrast (LIGHT THEME)
All values on --bg (#f4f6fa). WCAG AA requires >= 4.5:1 for normal text.

| Token | Before | Ratio | After | Ratio | Status |
|-------|--------|-------|-------|-------|--------|
| --acc | #2f6fe0 | 4.34:1 | #2767d8 | 4.83:1 | FIXED |
| --ok | #1f9d5b | 3.22:1 | #007d3b | 4.86:1 | FIXED |
| --warn | #c47a12 | 3.16:1 | #a45a00 | 4.80:1 | FIXED |
| --err | #d64545 | 4.05:1 | #c63535 | 4.90:1 | FIXED |
| --faint | #7a8699 | 3.41:1 | #626e81 | 4.77:1 | FIXED |
| --acc-active | #2f6fe0 | 4.34:1 | #2767d8 | 4.83:1 | FIXED |

Dark theme: all tokens PASS (lowest = --dim at 7.74:1). No changes needed.

### A5: Focus-Visible Styles
Present in ui/app.css lines 147-149: `outline:2px solid var(--focus); outline-offset:2px`
Applied to: #opsPanel button/input, #modeBar button, .seg button
Remaining gap: no global button:focus-visible rule (browser default applies elsewhere)

## Files Modified
- index.html: +aria-label on #edClose
- ui/tokens.css: 6 color values darkened in [data-theme=light] block

## Remaining for Full Closure
1. Live browser test: tab-through all panels, verify focus ring visible on every interactive element
2. Screen reader test (NVDA/VoiceOver): verify panel changes announced via aria-live
3. Add global `button:focus-visible` rule for consistent focus indication
4. aria-live attributes on dynamic content regions that receive JS updates without announcement

## Acceptance Criteria Status
- [x] Audit report shows 0 critical violations (static pass)
- [ ] Tab-through covers all interactive elements (needs live browser)
- [ ] Screen reader announces panel changes (needs live browser + SR)
