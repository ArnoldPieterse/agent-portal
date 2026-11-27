# Verifier Finding: stealth-ledger.md Schema vs Data Source Mismatch
Date: 2026-11-25 | Option (d) - concrete step on Scribe's oldest open goal

## Finding
Scribe's "Daily $ ledger" schema (memory/scribe/stealth-ledger.md) expects fields:
  outreach_staged, replies, demos, revenue_usd, per-WF {staged, replies, closed}

But the only data source (memory/builder/stealth/stealth-jobs.log.jsonl) records:
  ts, job, status(PASS/FAIL), elapsed_s, detail

**These are incompatible shapes.** The job log is operational (did the script run?), 
not business (how many invoices were sent, how much revenue closed).

## What Scribe needs to do
1. WF1-3 must write structured output files (e.g., wf1_output.json) containing 
   business metrics: {staged: N, replies: M, closed: K}
2. OR a separate harvest step reads the workflow output directories and aggregates
3. The job log can supplement with run-count/timestamp data but cannot alone populate the ledger

## Risk if unaddressed
Scribe will build the daily-entry script against stealth-jobs.log.jsonl, find zero 
business fields, and block on "no data to aggregate." 

## Recommended fix (for Builder or Scribe)
Add a --report-json flag to each WF that writes {staged, replies, closed} to a known path.
Then the ledger script reads: job log (timestamps/runs) + report JSONs (business metrics).

---
Evidence: memory/builder/stealth/run_stealth_jobs.py line ~45 (log_entry function), 
memory/scribe/stealth-ledger.md schema table, stealth-jobs.log.jsonl (3 entries, all operational).
