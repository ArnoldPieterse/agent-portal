# Staged outreach offer: Data entry / CRM updates (fill the blanks from the messy stuff)
date: 2026-11-26
kind: upload
platform: (unregistered - awaiting Arnold connection; fleet default voice)
status: drafting
topic: Outbound outreach pack - offer 3 of 3 (workflow arbitrage, STAGED ONLY)

## Body
Your CRM is full of blanks because someone has to type them in. We feed it from the messy stuff - emails, PDFs, voice notes, forms - and fill the fields for you. Anything we're not sure about gets flagged for a human glance instead of guessed. A virtual assistant does this at $19-35/hr; we do it flat, every month, without the hours adding up.

## Demo script (internal - run live in a call)
1. Drop 3-5 real-ish unstructured inputs (an email thread, a PDF, a transcribed voice note).
2. Run: extract entities -> map to the prospect's CRM schema -> show filled fields with confidence scores.
3. Highlight one low-confidence field that got flagged for human review (proves we don't guess).
4. Show the API write payload to their CRM (HubSpot/Pipedrive/Salesforce). Target: <5 min, unstructured in -> structured out.

## Pricing tiers (one-off -> subscription)
- One-off backfill: flat fee to clean + fill an existing pipeline backlog (~$150-300 one-time).
- Monthly subscription: $199-399/mo (tiered by record volume 200/500/1000+). Margin ~85-90% vs $4-25 LLM cost.
- Annual: 2 months free on prepay.

## Rationale
- Top-3 of Scribe's task-inventory top-3 (pure transcription, zero judgment, highest automatability score = 5).
- Pitch framing per SaaS-overlap analysis: CRMs STORE data, they don't FILL it; we're the clerk that populates them from unstructured sources. Zero overlap with the labor being automated.
- One concrete claim: $19-35/hr VA rate benchmark (sourced in Evidence).

## Evidence / sources (for Verifier fact-check before ship)
- memory/researcher/stealth/task-inventory.md: CRM row #3 ($19-35/hr, VA avg ~$19.22 US 2025); SaaS-overlap section (HubSpot Free 1M contacts, Pipedrive $14/user/mo, Salesforce $25/user/mo; LLM cost $4-25/mo; suggested $199-399/mo; margin 85-90%).
- Sources cited there: hirebasis.com (VA cost 2025), airtasker.com (VA cost).

fact-check:
- claim "$19-35/hr virtual assistant rate" -> PENDING Verifier/Researcher sign-off (source = task-inventory.md DRAFT v0.1; VA-rate sources not independently re-fetched this pass)
- claim "CRMs store but don't fill fields from unstructured input" -> PRODUCT POSITIONING (true of HubSpot/Pipedrive/Salesforce core function); confirm our extractor maps to their specific schema before ship

## Notes for ship
- STAGED ONLY - nothing is sent without Arnold's explicit approval.
- Needs: (1) a connected platform account, (2) Verifier sign-off on the $19-35/hr figure, (3) Builder confirmation of the CRM write path + confidence-flagging so "flagged for a human glance" is true.
- Wording + layout drafted by Designer as a wording-polish assist for Outlet's goal #11; Outlet owns voice/ship, Verifier owns fact-check. No internal IPs/paths/secrets in body.
