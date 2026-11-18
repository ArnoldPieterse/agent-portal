# Evidence: Goal #9 Keyboard Navigation (Builder c5)
Date: 2026-11-18

## Changes made:
1. **ui/app.css** - Replaced narrow `#opsPanel button:focus-visible,...` rule with global:
   `button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,a:focus-visible,[tabindex]:focus-visible`
2. **index.html** - Added aria-labels to icon-only buttons (addAgent, attach, edClose);
   added role="tablist" on mode nav; role="tab" + aria-selected on Solo/Group buttons.

## Verification:
- `python memory/builder/kb_nav_check.py` → 9 pass, 0 fail, 0 warn
- Checks: global focus ring CSS, icon-button ARIA, tablist semantics, Escape/Enter handlers,
  tabindex=0 on dynamic elements, aria-live status region, no positive tabindex.

## Remaining (browser-only):
- Visual confirm of focus ring rendering in a real browser (no headless browser in sandbox).
- Screen reader announcement test (requires NVDA/JAWS or VoiceOver).
