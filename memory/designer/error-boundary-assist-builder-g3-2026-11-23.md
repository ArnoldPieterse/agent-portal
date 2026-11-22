# Designer assist — Builder Goal 3 (Portal Error Boundary) — 2026-11-23

## What was done
Created `ui/error-boundary.js` (152 lines): a self-contained error boundary module providing:
- `UI.guard(fn, container, opts)` — wraps any async API call; on failure renders friendly error card + retry button
- `UI.showError(target, message, opts)` — inline error card with icon, message, optional detail line, retry CTA
- `UI.offlineBanner(show)` — sticky top-of-page strip when navigator.onLine is false; auto-wired to online/offline events
- `UI.onError()` — global unhandledrejection handler (suppresses console noise, shows toast/notify)

Design decisions:
- Uses existing CSS custom properties (--err, --panel, --br-md, --fs-*) so both light/dark themes work automatically
- No external dependencies; follows the same factory-function pattern as ui/components.js
- Retry button calls `UI.guard` recursively so the full error cycle repeats on retry
- ARIA: role="alert" on error card, aria-label on retry button

CSS added to `ui/app.css` (30 lines): .eb-card, .eb-icon, .eb-msg, .eb-detail, .eb-retry, .eb-offline, .eb-toast

## Structural verification
- Braces balanced: 26/26 JS, CSS balanced
- No syntax errors (manual review of IIFE pattern, arrow functions, template strings)

## Remaining for Builder to close goal #3
1. Wire `UI.guard()` into the 5 existing `.catch(()=>({}))` sites in core.js (L22, L23, L25, L122, etc.)
2. Add `<script src="/ui/error-boundary.js">` to index.html (before core.js)
3. Playwright acceptance: simulated 500 shows friendly message + retry; network disconnect shows offline banner; no unhandled rejections in console

## Files touched
- `ui/error-boundary.js` (NEW, 152 lines)
- `ui/app.css` (APPENDED 30 lines of .eb-* styles)
