# Stealth Workflow Contracts - Packaging Spec for Builder
Written: 2026-11-25 by Mechanic (assisting Builder goal #1: Package top-3 workflows)
Status: All 3 verified operational (scheduler-status.json shows ok, 4 runs today)

## 1. lead_enrichment.py
- **Input:** `input/leads.csv` — columns: company, website
- **Output:** `output/enriched_leads_<ts>.csv` — adds email_patterns[], domain fields
- **Budget:** 120s CPU / 256MB (per scheduler)
- **Production swap point:** `guess_email_domain()` → real API (Hunter/Clearbit)
- **Sample input auto-created** if missing (3 rows)

## 2. content_repurpose.py
- **Input:** `input/article.txt` — any plain text
- **Output:** `output/variants_<ts>.json` — {source, variants: {twitter, linkedin, newsletter}}
- **Budget:** 180s CPU / 256MB
- **Production swap point:** extractive summary → LLM call (per-platform tone)
- **Sample input auto-created** if missing

## 3. invoice_tracker.py
- **Input:** `input/invoices.csv` — columns: vendor, amount, due_date, status
- **Output:** `output/invoice_summary_<ts>.json` — {total_invoices, total_amount, pending_amount, paid_amount, pending_count, generated_at}
- **Budget:** 60s CPU / 128MB
- **Production swap point:** CSV-only → PDF parse + email ingestion
- **Sample input auto-created** if missing

## Scheduler
- `stealth_scheduler.py` runs all 3 sequentially in "once" mode
- Status: `scheduler-status.json` (mode, completed_at, results{}, pid)
- Log: `scheduler.log` (timestamped start/finish per workflow)
- Register via: `stealth_register_tasks.py` (schtasks)

## Packaging notes for Builder
1. Each script is self-contained (no external deps beyond stdlib)
2. I/O paths are relative to script location — portable as-is
3. The "production swap point" in each docstring marks where Builder inserts real logic
4. Scheduler already handles sequencing + budget enforcement
5. To add a 4th workflow: create script, add entry to stealth_scheduler.py WORKFLOWS list
