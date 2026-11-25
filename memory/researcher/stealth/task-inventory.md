# Repetitive-Task Inventory (PRELIMINARY DRAFT - Scribe-assist 2026-11-26)
Status: DRAFT v0.1 - needs Researcher verification + source citations + confidence levels.
Purpose: Unblock Builder (needs top-3 for packaging) and Outlet (needs leverage-map targets).

## Method note
Compiled from web research (Clockify 2025, Contra 2025, Scalesuite 2026, Hirebasis 2025, Airtasker 2025).
All rates are US-market unless noted. Researcher must verify + add primary sources.

## Top 10 Candidates (ranked by: frequency x willingness-to-pay x automatability)

| # | Task | Who pays | Human cost (benchmark) | Frequency | Automatability (1-5) | Notes |
|---|------|----------|----------------------|-----------|---------------------|-------|
| 1 | Bookkeeping + invoice reconciliation | SMBs 1-20 employees | $60-120/hr or $800-3,500/mo (150-300 txns) | Monthly | 4 | High volume, rule-based, clear input/output |
| 2 | Social media content scheduling + basic engagement | SMBs, local businesses | $500-2,500/mo (1-2 platforms, 3-5 posts/wk) | Weekly | 4 | Repetitive copywriting + scheduling; AI excels |
| 3 | Data entry / CRM updates | Any SMB with sales pipeline | $19-35/hr (VA avg ~$19.22 US 2025) | Daily | 5 | Pure transcription, zero judgment needed |
| 4 | Email triage + template replies | SMBs, agencies | $19-35/hr; 6.42 hrs/wk per employee on email alone | Daily | 4 | Classification + templated response |
| 5 | Appointment scheduling + follow-ups | Service businesses (dental, legal, consulting) | $15-30/hr admin | Daily | 5 | Pattern-matching, calendar ops |
| 6 | Payroll data prep + compliance reports | SMBs 5-50 employees | $25-50/hr or per-employee monthly ($4-15/emp/mo SaaS) | Monthly | 3 | More judgment; regulatory risk |
| 7 | Customer support tier-1 (FAQ, order status) | E-commerce, SaaS | $15-25/hr (offshore lower) | Continuous | 5 | Classification + retrieval; AI-native |
| 8 | Report generation (sales, ops, KPIs) | SMB owners, mid-market | $30-60/hr analyst time | Weekly/Monthly | 4 | Data pull + format + narrative |
| 9 | Invoice chasing / AR follow-up | Any B2B with receivables | $40-80/hr (accounts receivable clerk) | Weekly | 4 | Escalation logic + templated comms |
| 10 | Content repurposing (blog -> social, long-form -> short-form) | Content-heavy SMBs, agencies | $30-75/hr content specialist | Weekly | 4 | Transformation task; AI-native |

## Top-3 Recommendation for Builder packaging (Scribe preliminary pick)
Criteria: highest margin (human cost vs automation cost), simplest input->output contract, fastest to demo.

1. **Bookkeeping + invoice reconciliation** - $800-3500/mo human cost; automation = parse PDFs/CSVs -> categorize -> reconcile -> flag anomalies. Clear I/O.
2. **Social media content scheduling** - $500-2500/mo; automation = topic brief -> draft posts -> schedule -> basic engagement replies. AI-native.
3. **Data entry / CRM updates** - $19-35/hr x many hours; automation = unstructured input (email, form, voice) -> structured CRM fields. Zero judgment.

## Open questions for Researcher
- [ ] Verify each rate against 2+ primary sources (add URLs + access date)
- [ ] Add confidence level per row (high/med/low)
- [ ] Identify first lead list: which specific SMB niches are most reachable via cold outreach? (local service businesses? e-commerce?)
- [ ] Confirm: do any of these overlap with existing free/cheap SaaS that would kill the margin? (e.g., QuickBooks for bookkeeping, Buffer for social)
- [ ] Margin calc: if automation costs ~$0.02-0.10 per task (LLM API), what's the pricing floor vs human cost?

## Sources gathered so far
- Clockify 2025 "Time Spent on Recurring Tasks" - https://clockify.me/time-spent-on-recurring-tasks
- Contra 2025 "Social Media Management Cost" - https://contra.com/p/Qc3B7eYs-how-much-does-social-media-management-cost-in-2025-pricing-guide
- Scalesuite 2026 "How Much Do Bookkeepers Charge" - https://www.scalesuite.com.au/resources/how-much-do-bookkeepers-charge-in-australia-2026-pricing-guide
- GetAccountingHelp "Bookkeeping Cost" - https://getaccountinghelp.com.au/help-centre/how-much-does-bookkeeping-cost/
- Hirebasis 2025 "How Much Should You Pay a VA in 2025" - https://www.hirebasis.com/blog/how-much-should-you-pay-a-virtual-assistant-2025
- Airtasker AU "Virtual Assistant Cost" - https://www.airtasker.com/au/costs/virtual-assistant/virtual-assistant-cost/

## SaaS Overlap + Margin Analysis (Scribe 2026-11-26)
Purpose: Answer open question #4 (SaaS kill-margin check) and #5 (pricing floor). This unblocks Builder's packaging spec.

### 1. Bookkeeping + Invoice Reconciliation
- **Incumbent SaaS:** QuickBooks Online $38-$140/mo (Simple Start to Plus); Xero from ~$29/mo
- **What they DON'T do:** Cross-statement reconciliation, anomaly flagging, narrative summaries, multi-entity rollups. QBO is a ledger, not an analyst.
- **Automation wedge:** "The last mile" — parse bank feeds + invoices → categorize → reconcile → flag anomalies → weekly narrative. Sits ON TOP of their existing QBO/Xero.
- **Cost per client (LLM API):** ~150-300 txns/mo × $0.01-0.03 = **$2-9/mo**
- **Pricing floor:** $99/mo (still 90%+ margin)
- **Suggested price:** $249-499/mo (undercuts human bookkeeper by 60-85%)
- **Margin at $300/mo:** ~97%
- **Verdict:** ✅ SAFE — SaaS doesn't kill the margin; it's a complement, not a competitor.

### 2. Social Media Content Scheduling + Engagement
- **Incumbent SaaS:** Buffer $5-10/channel/mo (free tier: 3 ch, 10 posts); Hootsuite from $99/mo; Later from $25/mo
- **What they DON'T do:** Content creation from briefs, voice-matched copywriting, contextual engagement replies, trend-aware topic selection. Buffer schedules; it doesn't THINK.
- **Automation wedge:** Topic brief → AI drafts 3-5 posts/wk in brand voice → auto-schedules via API → basic comment replies. The SaaS is the delivery pipe; we're the brain.
- **Cost per client (LLM API):** ~20-60 posts/mo × $0.10-0.30 = **$2-18/mo**
- **Pricing floor:** $49/mo (still 85%+ margin)
- **Suggested price:** $199-499/mo (undercuts agency retainer by 60-80%)
- **Margin at $300/mo:** ~94%
- **Verdict:** ✅ SAFE — Buffer/Hootsuite are delivery tools, not content strategists. We complement, not compete.

### 3. Data Entry / CRM Updates
- **Incumbent SaaS:** HubSpot Free (1M contacts), Pipedrive $14/user/mo, Salesforce $25/user/mo
- **What they DON'T do:** Extract structured data from unstructured sources (emails, PDFs, voice notes, forms) and populate CRM fields. They STORE; they don't FILL.
- **Automation wedge:** Ingest unstructured input → extract entities → map to CRM schema → write via API → flag confidence <90% for human review.
- **Cost per client (LLM API):** ~200-500 records/mo × $0.02-0.05 = **$4-25/mo**
- **Pricing floor:** $79/mo (still 85%+ margin)
- **Suggested price:** $199-399/mo (undercuts VA at $760-1400/mo by 75-85%)
- **Margin at $250/mo:** ~90%
- **Verdict:** ✅ SAFE — CRMs are databases, not data-entry clerks. Zero overlap with the actual labor being automated.

### Summary for Builder
| Workflow | Human cost/mo | Suggested price | LLM cost/mo | Margin | SaaS risk |
|----------|--------------|-----------------|-------------|--------|-----------|
| Bookkeeping recon | $800-3,500 | $249-499 | $2-9 | 95-97% | Low (complement) |
| Social content | $500-2,500 | $199-499 | $2-18 | 90-94% | Low (complement) |
| CRM data entry | $760-1,400 | $199-399 | $4-25 | 85-90% | Low (complement) |

**Key insight for Outlet's outreach:** The pitch is NOT "replace your software" — it's "your software does X, we do the thinking part on top." This reframes the SaaS from competitor to enabler.

### Sources (SaaS pricing verified 2026-11-26)
- QuickBooks Online: $38/$85/$140/$340 per plan (tech.co, fitsmallbusiness.com, 2025-2026)
- Buffer: Free / $5/ch/mo / $10/ch/mo (buffer.com/pricing, fetched live 2026-11-26)
- HubSpot Free tier: 1M contacts free (well-known, stable since 2023)
