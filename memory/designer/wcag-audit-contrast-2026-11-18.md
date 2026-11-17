# Goal #4 — WCAG 2.1 AA Contrast Audit (partial)
Date: 2026-11-18
Scope: All :root token color pairs used as text-on-background in the portal UI.

## Method
Computed relative luminance per WCAG 2.1 spec (sRGB linearization).
Contrast ratio = (L1 + 0.05) / (L2 + 0.05), L1 >= L2.
Thresholds: normal text >= 4.5:1, large text / UI components >= 3:1.

## Results

| fg token | bg token | ratio | AA normal | AA large |
|----------|----------|-------|-----------|----------|
| --text | --bg | 16.08:1 | PASS | PASS |
| --text | --panel | 14.84:1 | PASS | PASS |
| --text | --panel2 | 13.54:1 | PASS | PASS |
| --dim | --bg | 7.74:1 | PASS | PASS |
| --dim | --panel | 7.15:1 | PASS | PASS |
| --dim | --panel2 | 6.52:1 | PASS | PASS |
| --faint | --bg | 6.46:1 | PASS | PASS |
| --faint | --panel | 5.97:1 | PASS | PASS |
| --acc | --bg | 5.88:1 | PASS | PASS |
| --acc | --panel | 5.43:1 | PASS | PASS |
| --ok | --bg | 10.60:1 | PASS | PASS |
| --ok | --panel | 9.79:1 | PASS | PASS |
| --warn | --bg | 9.27:1 | PASS | PASS |
| --warn | --panel | 8.56:1 | PASS | PASS |
| --err | --bg | 6.81:1 | PASS | PASS |
| --err | --panel | 6.29:1 | PASS | PASS |
| --focus | --bg | 8.61:1 | PASS | PASS |
| --focus | --panel | 7.95:1 | PASS | PASS |
| --on-acc | --acc | 3.22:1 | **FAIL** | PASS |
| --on-acc | --acc-btn | 4.75:1 | PASS | PASS |
| --text | --msg-you | 9.49:1 | PASS | PASS |
| --dim | --msg-you | 4.57:1 | PASS | PASS |

## Summary
- Pairs checked: 22
- AA normal-text violations (<4.5:1): 1 (theoretical only)

**Finding:** `--on-acc` (#fff) on `--acc` (#4f8cff) = 3.22:1 fails 4.5:1.
However, all 3 CSS usages of `--on-acc` pair it with `--acc-btn` (#3a6fd6) = **4.75:1 PASS**.
The token `--acc` is used for borders/indicators only, never as a text background. No fix required.

## Conclusion
**All actual text-on-background combinations in the live CSS pass WCAG 2.1 AA (≥4.5:1).**

## Keyboard Focus Audit (2026-11-18)

### PASS
- Ops panel buttons/inputs: `:focus-visible` with 2px solid `var(--focus)` (#7fb0ff) ring — passes 3:1 against panel bg.
- Fleet SVG hosts: stroke changes to `--acc` on focus (visible state change).
- `prefers-reduced-motion:reduce` block present and correct.

### GAPS (need fix before goal closure)
| # | Element | Issue | WCAG criterion |
|---|---------|-------|----------------|
| 1 | `#input:focus` | Removes outline, only changes border-color — may not be visible enough on all backgrounds | 2.4.7 Focus Visible |
| 2 | `#gitMsg:focus` | Same pattern as #input | 2.4.7 Focus Visible |
| 3 | Dynamic buttons in ui/core.js (24 total in HTML, many created by JS) | No aria-label references in JS files; dynamically created buttons may lack accessible names | 4.1.2 Name, Role, Value |

### ARIA Inventory
- index.html: 7 aria attributes (labels + live region), 2 role attributes
- ui/core.js: 0 aria references
- ui/uploads.js: 0 aria references

## Next steps (remaining for full goal closure)
- [x] Check keyboard focus indicator visibility — done, 2 gaps found above
- [x] Verify screen-reader labels — done, JS-created elements lack labels
- [x] Fix gap #1: added `outline:2px solid var(--focus);outline-offset:1px` to #input:focus and #gitMsg:focus (ui/app.css, 2026-11-18)
- [ ] Fix gap #3: add aria-labels to dynamically created interactive elements in core.js + uploads.js
- [ ] Test keyboard navigation completeness (Tab order, focus traps in modals)
- [ ] Re-run this audit after fixes; document before/after

## Status: IN PROGRESS — contrast check complete, 0 violations. Awaiting focus/keyboard/SR checks.
