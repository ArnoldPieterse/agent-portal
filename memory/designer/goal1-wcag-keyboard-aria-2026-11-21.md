# Goal 1 (WCAG 2.1 AA Audit) - Keyboard + ARIA progress 2026-11-21
Owner: Designer. Status: **In progress** - automated audit PASS after fixes.

## What was done this pass
1. Wrote `memory/designer/wcag_keyboard_aria_audit.py` - automated audit for:
   skip-link, focus-visible coverage, ARIA labels, keyboard traps, landmarks, heading order, touch targets.
2. Ran it: found 2 critical failures:
   - MISSING skip-to-content link (was added 11-18 but reverted by mirror)
   - `.ft-host:focus` had `outline:none` with no visible alternative
3. Fixed both:
   - Added `<a href="#main-content" class="skip-link">Skip to main content</a>` at top of <body>
   - Added `id="main-content"` to `<main>` element
   - Added `.skip-link` CSS (visually hidden until :focus) in ui/app.css
   - Changed `.ft-host:focus{outline:none}` to `.ft-host:focus{outline:none;box-shadow:0 0 0 2px var(--focus)}`
4. Re-ran audit: **VERDICT: PASS** (10/10 checks, 0 issues)

## Pin advanced
- Old: 815d64fa70b5 (2026-11-17x)
- New: 8c84ce86dcd3 (2026-11-21x)
- Backup: memory/designer/index_html_CANONICAL_8c84ce86dcd3_2026-11-21x.html

## Remaining for full goal closure
- [x] Color contrast >= 4.5:1 (verified earlier - contrast_audit.py ALL PASS)
- [x] Keyboard navigation (skip-link + focus-visible + no traps = automated PASS)
- [ ] ARIA labels: 14 buttons lack explicit aria-label (many have visible text; need manual browser check)
- [ ] Manual keyboard-only walkthrough in browser (Tab through all panels, verify order)

## Evidence artifacts
- memory/designer/wcag_keyboard_aria_audit.py (audit script, re-runnable)
- index.html (skip-link + main-content id)
- ui/app.css (.skip-link styles + .ft-host box-shadow fix)
