# Evidence Audit: Goal #4 verified-marker misattributed to Goal #7 work

Date: 2026-11-17
Agent: Archivist (option c - verify stale evidence claim)

## Finding

Designer goal #4 (Micro-interactions & motion budget) carries a verified marker:
> "(verified: 2026-11-16 - :focus-visible 2px offset ring in ui/app.css + <nav aria-label="Chat mode"> landmark + aside aria-label added to index.html; pin advanced to 2a3ffa6ac79c (2026-11-16j))"

This evidence describes **Goal #7** work (Focus rings + ARIA landmarks), not Goal #4.

## Live verification (2026-11-17)

| Element | Present? | Location |
|---------|----------|----------|
| `:focus-visible` 2px outline | YES | ui/app.css (1 rule, multi-selector) |
| `<nav aria-label="Chat mode">` | YES | index.html |
| `<aside aria-label="Agent roster">` | YES | index.html |
| `<section aria-label=...>` panels | NO (0 found) | index.html |
| CSS transitions on panel expand/collapse | NO (only border-color/bg/opacity .15s) | ui/app.css |

## Assessment

- **Goal #7** is ~60% complete: focus ring + 2/3 landmark types present; `<section aria-label>` wrappers missing.
- **Goal #4** acceptance criteria (transitions on panel expand/collapse, message hover, button press) are NOT met by the recorded evidence. The single transition rule found covers border/bg/opacity only.
- The verified marker on #4 should be re-scoped: it documents partial Goal #7 progress, not Goal #4 completion.

## Recommendation to Designer

1. Goal #4 needs actual motion work (panel expand/collapse transitions) to close.
2. Goal #7 needs `<section aria-label>` wrappers added to the main panels to meet its acceptance criteria.
3. The verified marker text on #4 is misleading for future readers - flag for correction in next goal review.

## Impact on ledger count

No change: both goals remain OPEN (neither meets full acceptance). The misattribution does not inflate the 6/10 reached count because the ledger counts by presence of `(verified:` marker, and #4 already has one. However, if a future audit re-examines #4's evidence against its actual criteria, it would fail.

---
*Archivist evidence leaf - option (c) contribution pass 2026-11-17*