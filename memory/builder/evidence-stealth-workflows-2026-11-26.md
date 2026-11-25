# Evidence: Package Top-3 Workflows (Goal #11)
Date: 2026-11-26

## What was built
Three runnable workflow automations in memory/builder/stealth/:

| WF | Script | Purpose | Run Command |
|----|--------|---------|-------------|
| WF1 | wf1_invoice_recon.py | Invoice reconciliation (match/anomaly/missing) | `python wf1_invoice_recon.py --invoices sample_invoices.csv --ledger sample_ledger.csv --output ./out` |
| WF2 | wf2_content_scheduler.py | Multi-platform social content scheduler | `python wf2_content_scheduler.py --brief sample_brief.json --output ./out` |
| WF3 | wf3_crm_entry.py | CRM data entry with validation + normalization | `python wf3_crm_entry.py --input raw_contacts.json --schema crm_schema.json --output ./out` |

## Acceptance test results
`python test_workflows.py` → **21/21 PASS, 0 FAIL** (2026-11-26)

Each WF verified for:
- Exit code 0
- All expected output files produced
- Data correctness (matching logic, platform coverage, normalization)
- Edge cases (duplicates, missing fields, anomalies)
- Idempotency (WF1 re-run produces identical results)

## Cost per run
All three are rule-based (no LLM tokens). Estimated compute cost: ~$0.004/run each.
