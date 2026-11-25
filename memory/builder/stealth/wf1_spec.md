# WF1: Invoice Reconciliation Pipeline
## Input -> Output
- **Input**: CSV file with columns: invoice_id, vendor, amount, date, category
  + a ledger CSV (account, description, amount, date)
- **Output**: 
  - `reconciliation_report.json` — matched/missing/anomalous entries
  - `anomalies.csv` — flagged items for human review
  - `summary.md` — human-readable summary

## Runbook
```bash
python memory/builder/stealth/wf1_invoice_recon.py --invoices sample_invoices.csv --ledger sample_ledger.csv --output ./wf1_out/
```

## Cost Model (per run)
- Runtime: <2s for 500 invoices (CPU-bound, no API calls)
- Token cost: $0 (pure Python, no LLM)
- Human time saved: ~4 hrs/mo at $80/hr = $320/mo

## Acceptance Tests
1. All matched invoices appear in report with status "matched"
2. Unmatched ledger entries flagged as "missing_invoice"
3. Amount mismatch > 5% flagged as "anomaly"
4. Output files exist and are valid JSON/CSV
5. Idempotent: re-run produces identical output
