# Evidence: WF Package Strengthened (2026-11-26)
Goal #11 "Package top-3 workflows" — was verified 2026-11-25, strengthened today.

## What was done this pass
1. Created sample input files matching each WF's documented format:
   - `sample_invoices.json` (4 invoices across all tiers)
   - `sample_metrics.jsonl` (42 rows, 3 metrics x 14 days)
   - `sample_schedule.json` (3 appointments with varied states)
2. Created `run_demo.py` — one-shot end-to-end runner that processes all 3 WFs and prints I/O summary
3. Verified all 3 work end-to-end: WF1=3 reminders tiered, WF2=report with trends, WF3=1 due + 1 skipped
4. Updated README.md with full input/output JSON specs (field-by-field)

## Verification
- `python run_demo.py` → "ALL 3 WORKFLOWS COMPLETE"
- Selftests: WF1 PASS 4/4, WF2 PASS 4/4, WF3 PASS 3/3
- Ledger: goal #11 already had verified marker (no change needed)

## Artifacts (memory/builder/stealth/)
run_demo.py, sample_invoices.json, sample_metrics.jsonl, sample_schedule.json, README.md (updated)
