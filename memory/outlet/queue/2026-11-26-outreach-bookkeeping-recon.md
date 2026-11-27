# Staged outreach offer: Bookkeeping + invoice reconciliation (last mile on top of QBO/Xero)
date: 2026-11-26
kind: upload
platform: (unregistered - awaiting Arnold connection; fleet default voice)
status: drafting
topic: Outbound outreach pack - offer 1 of 3 (workflow arbitrage, STAGED ONLY)

## Body
You already run QuickBooks or Xero. They keep the books; nobody does the thinking. We sit on top of what you have and do the last mile: read your bank feeds and invoices, categorize them, reconcile, flag the odd ones out, and hand you a plain-English note each week. You stop being the bookkeeper. A 1-20 person business pays $800-3,500/mo for this by hand - we do it for a fraction of that.

## Demo script (internal - run live in a call)
1. Open a shared folder with 3-5 sample bank CSVs + 2 PDF invoices (use the prospect's own if they share).
2. Run the reconciliation workflow: parse -> categorize -> match to ledger -> flag anomalies.
3. Show the output: a categorized list, the reconciled totals, and the 1-2 flagged items with reasons.
4. Read back the plain-English weekly note aloud. Target: <5 min, one real input -> one clean output.

## Pricing tiers (one-off -> subscription)
- One-off setup / pilot: flat fee for a single month's reconciliation + onboarding (~$150-300, undercuts human monthly cost).
- Monthly subscription: $249-499/mo (tiered by txn volume 150/300/600+). Margin ~95-97% vs $2-9 LLM cost.
- Annual: 2 months free on prepay (lock in the recurring revenue the engine targets).

## Rationale
- Top-1 of Scribe's task-inventory top-3 (highest human-cost wedge, clearest I/O contract, fastest to demo).
- Pitch framing per SaaS-overlap analysis: NOT "replace your software" - it sits ON TOP of QBO/Xero. Reframes the incumbent from competitor to enabler.
- One concrete claim: $800-3,500/mo human cost benchmark (sourced in Evidence).

## Evidence / sources (for Verifier fact-check before ship)
- memory/researcher/stealth/task-inventory.md: bookkeeping row #1 ($800-3,500/mo for 150-300 txns); SaaS-overlap section (QBO $38-140/mo, Xero ~$29/mo; LLM cost $2-9/mo; suggested $249-499/mo; margin 95-97%).
- Sources cited there: scalesuite.com + getaccountinghelp.com (bookkeeper rates), QuickBooks/Xero pricing (tech.co, fitsmallbusiness.com).

fact-check:
- claim "$800-3,500/mo human bookkeeping cost" -> PENDING Verifier/Researcher sign-off (source = task-inventory.md DRAFT v0.1, marked "needs Researcher verification"; not independently re-run)
- claim "sits on top of QBO/Xero, does not replace it" -> PRODUCT POSITIONING (design framing, not a factual market claim); confirm workflow actually ingests QBO/Xero exports before ship

## Notes for ship
- STAGED ONLY - nothing is sent without Arnold's explicit approval.
- Needs: (1) a connected platform account, (2) Verifier sign-off on the $800-3,500 figure, (3) Builder confirmation the recon workflow ingests QBO/Xero exports so the "on top of" claim is true.
- Wording + layout drafted by Designer as a wording-polish assist for Outlet's goal #11; Outlet owns the voice/ship decision, Verifier owns fact-check. No internal IPs/paths/secrets in body.
