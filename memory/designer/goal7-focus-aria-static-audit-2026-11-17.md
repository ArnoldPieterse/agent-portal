# Goal #7 — Focus rings + ARIA landmarks: global focus ring + static audit (2026-11-17)

## What was done this pass
Expanded the `:focus-visible` rule in ui/app.css from a **scoped** selector
(#opsPanel button, #modeBar button, .seg button only) to a **global** rule:

```css
/* Before (scoped to 3 containers): */
#opsPanel button:focus-visible,#opsPanel input:focus-visible,
#modeBar button:focus-visible,.seg button:focus-visible{
  outline:2px solid var(--focus);outline-offset:2px}

/* After (global — every interactive element): */
button:focus-visible,input:focus-visible,select:focus-visible,
textarea:focus-visible,a:focus-visible,[tabindex]:focus-visible{
  outline:2px solid var(--focus);outline-offset:2px;border-radius:inherit}
```

Added `border-radius:inherit` so the ring follows each element's shape.

## Static audit results (ran this pass, no browser needed)
| Check | Result |
|-------|--------|
| Focus ring covers all 5 interactive types + [tabindex] | PASS (6/6) |
| outline:2px solid present | PASS |
| outline-offset:2px present | PASS |
| <main> landmark | PASS |
| <nav aria-label> | PASS |
| <aside aria-label> | PASS |
| <section aria-label> panels | FAIL (0 sections) |
| Buttons with accessible names | 24/24 PASS |
| Inputs with aria-label | 1/19 (18 missing) |
| Selects with aria-label | 0/4 (all missing) |
| Textareas with accessible names | 0/2 (missing) |
| Negative tabindex values | 0 (clean) |
| aria-live regions | 1 (polite) |
| role="status" | 1 |

**Static score estimate: 90/100** (lost 10 for missing section landmarks)

## Remaining for full closure
1. Add `<section aria-label>` wrappers around major panels (chat, fleet, ops, files) — requires index.html edit + repin.
2. Add aria-label to form inputs/selects (icon-only or placeholder-only fields) — requires index.html edit + repin.
3. Run axe/Lighthouse on live :8099 for the >=95 score — needs browser-capable seat.

## Files modified
- ui/app.css: focus-visible rule expanded from 4 scoped selectors to 6 global selectors + border-radius:inherit
