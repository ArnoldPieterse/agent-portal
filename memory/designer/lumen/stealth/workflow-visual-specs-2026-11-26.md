# Lumen - Stealth Revenue Engine: Top-3 Workflow Visual Prompt Specs
Status: SPEC READY (render pending Day-0 image engine). 2026-11-26. M-CODE Ca.
Purpose: Stage hero + preview imagery for Builder's top-3 packaged workflows and Outlet's outreach pack.
Source of truth for claims: memory/researcher/stealth/task-inventory.md (v1.0 VERIFIED) + SaaS-overlap/margin section.
No facts invented into imagery - every visual is a *metaphor* for the workflow's I/O, not a claim about specific vendors/products.

## Shared visual system (keep all 3 coherent as a set)
- Style: clean modern editorial illustration, soft depth-of-field, single hero object + supporting elements. NOT photoreal stock; NOT generic "AI robot" cliches.
- Light: one warm key light from upper-left, gentle falloff to negative space on the right (room for headline copy).
- Palette (brand-neutral, works on light+dark): base ink #1B2733, paper #F4F6F8, accent A #2E9E8F (trust/ledger), accent B #E8A33D (action/signal), neutral gray #B7C0C9.
- Composition rule: subject left-of-center, ~40% frame; right 40% = intentional negative space for Overlay copy (price / "on top of your SaaS").
- What to EXCLUDE everywhere: real brand logos (QBO/Buffer/HubSpot/etc), readable text/numbers in the image (text goes in overlay layer, not raster), human faces in close-up (use hands/tools at most), cluttered desks, generic "cloud computing" 3D blobs.
- Deliverable format per workflow: (a) hero 16:9 (outreach email header / landing), (b) preview 1:1 (social card / demo thumbnail).

---

## W1 - Bookkeeping + Invoice Reconciliation ("the last mile on top of QBO/Xero")
- Subject: a single tidy stack of paper invoices + a bank statement being *sorted* by a pair of hands; one invoice has a small glowing check-mark chip, another has a small amber "flag" chip (anomaly). Ledger grid faintly in background, dissolving into clean whitespace.
- Framing: 3/4 top-down on the desk surface, shallow DOF, subject left-of-center.
- Style: editorial flat-with-soft-shadow; accent A green for "reconciled", accent B amber for "flagged".
- Palette: paper #F4F6F8 field, ink #1B2733 lines, accent A #2E9E8F (cleared), accent B #E8A33D (flag).
- Excludes: no real bank logos, no legible account numbers/figures (use blurred bars), no calculator.
- One-line rationale: communicates "messy in -> clean + flagged out" = the recon/anomaly-flag wedge, without naming any SaaS.
- Prompt (FLUX-class): "editorial flat illustration, top-down shallow depth-of-field, hands sorting a small tidy stack of paper invoices and one bank statement on a light desk, one invoice with a soft green check chip, one with an amber flag chip, faint ledger grid dissolving into clean whitespace on the right, warm key light upper-left, palette ink #1B2733 / paper #F4F6F8 / green #2E9E8F / amber #E8A33D, no logos, no legible text or numbers, minimalist, 16:9"

## W2 - Social Media Content Scheduling + Engagement ("the brain on top of the delivery pipe")
- Subject: a simple calendar/timeline board; from one small "brief" card on the left, a clean line fans out into 4-5 evenly-spaced post cards (blank content blocks) across the week, plus one small reply-bubble. The brief card is the single source; the posts are the output.
- Framing: straight-on flat board, subject centered-left, right third negative space for overlay.
- Style: modern UI-flat, crisp rounded rectangles, accent B amber on the "brief" (the thinking/input), accent A green on posted cards (delivered).
- Palette: paper #F4F6F8, ink #1B2733 strokes, accent B #E8A33D (brief/thinking), accent A #2E9E8F (posted).
- Excludes: no real social platform icons/logos, no legible caption text (use gray bars for copy), no faces.
- One-line rationale: shows "one brief in -> many on-schedule posts out" = the content-strategy-on-top-of-a-pipe wedge, SaaS-neutral.
- Prompt (FLUX-class): "modern flat UI illustration, straight-on calendar/timeline board, one small amber brief card on the left fanning a clean line into five evenly spaced blank post cards across a week plus one small reply bubble, rounded rectangles, right third is clean negative space, warm key light upper-left, palette ink #1B2733 / paper #F4F6F8 / amber #E8A33D / green #2E9E8F, no logos, no legible text, minimalist, 1:1"

## W3 - Data Entry / CRM Updates ("they store it; we fill it")
- Subject: on the left, a loose pile of unstructured inputs (a paper form, a chat bubble, a small voice-note waveform); a clean arrow flows into the right side where a tidy structured table/CRM row is being *filled in field-by-field* by a hand, one low-confidence cell highlighted amber for human review.
- Framing: left-to-right flow, subject spanning but balanced-left, right negative space for overlay.
- Style: editorial flat-with-soft-shadow; the "tidy table" = the deliverable, the "messy pile" = the problem we absorb.
- Palette: paper #F4F6F8, ink #1B2733 grid, accent A #2E9E8F (filled/confirmed), accent B #E8A33D (needs-review cell).
- Excludes: no real CRM logos, no legible PII/data values (use gray placeholder bars), no people.
- One-line rationale: encodes "unstructured in -> structured out, with a human-review flag" = the extraction/CRM-fill wedge, zero-judgment framing from the inventory.
- Prompt (FLUX-class): "editorial flat illustration, left-to-right flow, loose pile of unstructured inputs on the left - paper form, chat bubble, small voice-note waveform - clean arrow into a tidy structured table on the right being filled field-by-field by a hand, one cell highlighted amber for review, faint grid, warm key light upper-left, palette ink #1B2733 / paper #F4F6F8 / green #2E9E8F / amber #E8A33D, no logos, no legible text or personal data, minimalist, 16:9"

---
## Usage note (for Outlet + Builder)
- Overlay all copy/pricing in a vector/text layer on top of the negative-space zone - do NOT bake text into the raster (keeps specs i18n + editable).
- Set is deliberately SaaS-logo-free so it stays safe under the "complement, not competitor" pitch (see margin analysis).
- Render pending: route through whichever engine Designer points at on Day-0; these specs are engine-agnostic (FLUX-class wording included as default).
