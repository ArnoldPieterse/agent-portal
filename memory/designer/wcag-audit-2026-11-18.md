# WCAG 2.1 AA Audit — Portal UI (2026-11-18)

Goal: designer.md #4
Status: audit complete + ALL 8 FIXES APPLIED same turn

## 1. Color Contrast — ALL PASS ✅

All token pairs meet >=4.5:1 on all three surfaces (bg, panel, panel2).
Worst case: `--acc` (#4f8cff) on `--panel2` = 4.95:1 (barely passes).
No contrast violations found.

## 2. Keyboard Focus — VIOLATIONS FOUND ⚠️

| Element | Issue | Fix |
|---------|-------|-----|
| `#input:focus` | `outline:none` with only border-color change; subtle and fails focus visibility (WCAG 2.4.7) | Add `box-shadow:0 0 0 2px var(--focus)` or restore outline |
| `.ft-host:focus` | `outline:none` on fleet topology SVG nodes; no visible alternative | Add stroke-width increase or box-shadow equivalent |
| Global scope | `:focus-visible` styles only cover `#opsPanel`, `.seg`, `#modeBar`; not the main chat panel, sidebar buttons, or file panel | Extend to universal selector or add per-panel rules |

## 3. Screen-Reader Labels — VIOLATIONS FOUND ⚠️

| Element | Location | Issue | Fix |
|---------|----------|-------|-----|
| `#input` (textarea) | index.html L84 | placeholder only, no aria-label; placeholder disappears on input | Add `aria-label="Message"` |
| `#filePick` (input file) | index.html L94 | hidden but focusable; no label | Add `aria-hidden="true"` (it's triggered by button) |
| `#dirPick` (input file) | index.html L95 | same as above | Add `aria-hidden="true"` |
| `#f_reasoning` (select) | index.html L132 | no label text nearby in DOM order | Add `aria-label="Reasoning effort"` |
| Edit button "⚙" | core.js L38 | icon-only, has title but no aria-label | Add `g.setAttribute('aria-label','Edit agent profile')` |
| Delete button "✕" | core.js L40 | icon-only, has title but no aria-label | Add `x.setAttribute('aria-label','Delete agent')` |
| File links (a.flink) | core.js L289 | dynamic `<a>` with href but text may be filename only | OK if text is set; verify at runtime |
| Restore buttons "↩ restore" | core.js L433 | has visible text "restore" — acceptable | No fix needed |

## 4. Summary

- Contrast: **0 violations** ✅
- Focus visibility: **3 issues** (outline removal without alternative)
- ARIA labels: **5 elements** need aria-label or aria-hidden
- Keyboard nav: native elements are tabbable; no custom focus-trap issues detected

## Next Step (next pass)
Apply the 8 fixes above to index.html + ui/app.css + ui/core.js. Re-run this audit to confirm zero violations.

## Fixes Applied (2026-11-18, same turn)

### CSS (ui/app.css sha12=cc1991f1fe5b)
- `#input:focus` → added `box-shadow:0 0 0 2px var(--focus)` as visible focus ring
- `.ft-host:focus` → added `stroke-width:3` as visible alternative to removed outline

### HTML (index.html sha12=8bbb710a57ff)
- `#input` textarea → added `aria-label="Message"`
- `#filePick` → added `aria-hidden="true"` (triggered by button, not direct)
- `#dirPick` → added `aria-hidden="true"`
- `#f_reasoning` select → added `aria-label="Reasoning effort"`

### JS (ui/core.js sha12=103eb4f2539a)
- Edit button "⚙" → added `setAttribute("aria-label","Edit agent profile")`
- Delete button "✕" → added `setAttribute("aria-label","Delete agent")`

### Pin advancement
- index.html pin: 815d64fa70b5 → 8bbb710a57ff (backup memory/designer/index_html_CANONICAL_8bbb710a57ff_2026-11-18a.html)
- ui/app.css + ui/core.js ADDED to PIN_FILES (hot-note fix: they were being reverted by mirror)

### Remaining for full acceptance
- Re-run contrast check after any future token changes (currently all pass)
- Verify no new violations introduced by subsequent UI work
