# Goal 10 Progress: Page-break rules added to @media print
Date: 2026-11-19 (Designer auto-loop)

## What was done
Added missing page-break and @page rules to `ui/app.css` @media print block:
- `@page{margin:14mm;}` — proper page margins for print
- `animation:none !important;transition:none !important;` on universal selector — flattens motion
- `break-inside:avoid` on `.panel,[id$="Panel"]` — prevents panels splitting across pages
- `h1,h2,h3,.panel-title,.mh-card h3{break-after:avoid;}` — headings don't orphan at page bottom
- `table,tr{break-inside:avoid;}` — table rows stay together

## Verification (static)
- Braces balanced: 313/313 ✓
- All 5 new rules confirmed present via grep ✓
- Print button injection in core.js L467-471 confirmed intact ✓
- `--print-dim` token defined in tokens.css ✓

## Remaining for acceptance
Browser print-preview render (Ctrl+P / window.print()) to confirm:
- Clean white layout, no cut-off content
- Page breaks fall between sections not mid-card
- Interactive elements hidden

This is the same pale-sandbox CDP blocker as Goals 2/5/6/8/9 — non-sandbox seat required.

## File changed
- `ui/app.css` (347 lines, 29921 bytes)