# Goal #4 — WCAG 2.1 AA Accessibility Audit (Consolidated)
Date: 2026-11-18 | Owner: Designer | Status: IN PROGRESS (fixes landed, remaining items documented)

## Scope
Full static audit of ui/app.css + index.html + ui/core.js + ui/uploads.js for WCAG 2.1 AA compliance across:
1. Color contrast (SC 1.4.3) — >=4.5:1 normal, >=3:1 large text
2. Keyboard navigation (SC 2.1.1) — all functionality operable via keyboard
3. Screen reader labels (SC 4.1.2) — name, role, value on interactive elements
4. Motion (SC 2.3.3) — prefers-reduced-motion respected

## Results Summary

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Color contrast >=4.5:1 | **PASS** | 21 token pairs + 8 hardcoded pairs all pass; min ratio 4.75:1 (see wcag_aa_dark_theme_audit_2026-11-17.md) |
| Keyboard navigation | **PARTIAL** | Buttons/inputs natively focusable; panel heads (.dhead) NOT keyboard operable (no tabindex, no keydown handler) |
| Screen reader labels | **PASS** (buttons) / **GAP** (panels) | All 24 buttons have visible text or aria-label; .dhead divs lack role="button" + aria-expanded |
| Motion preference | **FIXED THIS PASS** | @media(prefers-reduced-motion:reduce) added to ui/app.css line 270; all transitions/animations disabled when set |

## What was fixed this pass (2026-11-18)

### ui/app.css — prefers-reduced-motion block added
```css
/* WCAG 2.1 AA: Respect user motion preferences (goal #4) */
@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition-duration:0.01ms!important;animation-duration:0.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important}}
```
Location: end of file, after .ft-empty rule. No pin advance needed (CSS is not pinned).

## Remaining gaps (require index.html edit + pin advance)

| Gap | SC violated | Fix needed |
|-----|-------------|------------|
| .dhead divs not keyboard operable | 2.1.1 (Keyboard) | Add tabindex="0" to each .dhead; add keydown handler in core.js for Enter/Space |
| Panel toggle state not exposed | 4.1.2 (Name, Role, Value) | Add role="button" + aria-expanded="true/false" to .dhead elements; JS updates on toggle |
| No :focus-visible on .dhead specifically | 2.4.7 (Focus Visible) | Universal :focus-visible rule covers it IF tabindex is present — no extra CSS needed |

## Verification method
- Contrast: python script (memory/designer/wcag_aa_contrast_check.py) computes WCAG relative luminance for all fg/bg pairs in :root + hardcoded values
- Keyboard: grep for tabindex/keydown/focus events across HTML+JS
- ARIA: regex extraction of role/aria-* attributes from index.html
- Motion: grep for @media(prefers-reduced-motion) + max transition duration (200ms confirmed)

## Acceptance criteria status
- [x] Audit leaf with before/after contrast ratios — DONE (this file + wcag_aa_dark_theme_audit)
- [ ] Zero AA violations remaining — BLOCKED on index.html pin advance for .dhead tabindex/role fixes
- Next step: apply the 2-line fix to each .dhead in index.html, advance pin, re-run this audit

## Files touched this pass
- ui/app.css (prefers-reduced-motion block appended)
- memory/designer/wcag-aa-audit-consolidated-2026-11-18.md (this file)
