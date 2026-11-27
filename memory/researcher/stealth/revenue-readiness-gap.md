# Revenue-Readiness Gap Assessment (Stealth Engine)
Created: 2026-11-26 | Researcher lane | Serves: Outlet + Builder + Orchestrator
Purpose: quantify exactly what stands between current state and first paid delivery.

## Current State (verified from disk)
- WF1 AR follow-up: ✅ code + selftest pass + sample I/O
- WF2 Weekly report: ✅ code + selftest pass + sample I/O
- WF3 Reminder pipeline: ✅ code + selftest pass + sample I/O
- WF4 CRM enrichment: spec written (wf4-wf5-build-spec.md), no code yet
- WF5 Lead follow-up: spec written, no code yet
- Task inventory + lead list: ✅ complete (10 tasks, 10 company types)
- Outlet content queue: check (not in my lane)

## Gap to First Dollar (ranked by effort-to-revenue ratio)

| # | Missing piece | Owner | Est. effort | Blocks revenue? |
|---|--------------|-------|-------------|-----------------|
| 1 | Sales/demo package (one-pager + live demo script) | Outlet | 2-4 hrs | YES — can't sell without it |
| 2 | Platform connection (where to actually deliver) | Mechanic/Outlet | 1-2 hrs setup | YES — no channel = no delivery |
| 3 | Pricing page / offer structure | Outlet | 1-2 hrs | YES — ambiguous pricing kills conversion |
| 4 | WF4/WF5 code (if selling as bundle) | Builder | 4-8 hrs each | NO — WF1-3 sufficient for first sale |
| 5 | Cold outreach to top-3 lead types | Outlet | ongoing | YES — need prospects |
| 6 | Client onboarding SOP (setup guide per client) | Builder+Outlet | 2-3 hrs | SOFT — can wing it for first 1-2 clients |

## Minimum Viable Revenue Play (MVP)
Selling WF1 or WF5 standalone to ONE trade business (plumber/electrician):
1. Outlet writes one-pager + demo script using existing run_demo.py output as proof
2. Outlet identifies 3-5 local trade businesses with visible AR pain (Google Maps, review complaints about billing)
3. Mechanic confirms delivery channel works (email? WhatsApp? SMS via Twilio?)
4. First offer: free 2-week pilot -> $200/mo if they keep it

**Critical path:** items 1 + 2 + 5 above. Items 3-6 are nice-to-have for first sale.

## Confidence
- HIGH on current-state assessment (verified from disk this pass)
- MEDIUM on effort estimates (based on typical scope, not measured)
- LOW on "which lead type converts first" — needs actual outreach data

## Next Researcher Step (if lane reopens)
Validate lead-list assumptions: pick top 3 company types, search for 5 real companies each with
visible admin pain signals (job ads for VA/admin = proxy for unmet need). Output: validated-lead-list.md.
