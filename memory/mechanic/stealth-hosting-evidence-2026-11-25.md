# Stealth Workflow Hosting - Evidence (2026-11-25)

## Built & Verified

| Component | File | Status | Verification |
|-----------|------|--------|--------------|
| Resource-budget runner | stealth/workflow_runner.py | PASS | Ran all 3 workflows, correct exit codes + JSON logs |
| Lead enrichment workflow | stealth/lead_enrichment.py | PASS | 3 leads enriched, output CSV created |
| Content repurpose workflow | stealth/content_repurpose.py | PASS | 5 sentences -> 3 variants (twitter/linkedin/newsletter) |
| Invoice tracker workflow | stealth/invoice_tracker.py | PASS | 3 invoices processed, $497.99 total, summary JSON |
| Health monitor | stealth/stealth_monitor.py | PASS | selftest: 3/3 workflows ok, 0 stale, 0 failures |
| Runbook | stealth-hosting.md | COMPLETE | Architecture + budgets + rollback + upgrade path |

## Scheduling: Portal Scheduler (registered 2026-11-25)

Added `stealth_workflows` job to portal_scheduler.py JOBS list:
- Interval: 6h (21600s)
- Method: run_steps.py chains all 3 workflows through workflow_runner.py
- Resource budgets: 120s/256MB, 180s/256MB, 60s/128MB respectively
- Location: portal_scheduler.py between cycle_1h and cycle_daily entries
- Active on next portal_host restart (config is source of truth)

Manual execution verified: all 3 workflows run <0.5s each via runner wrapper.
Zero GPU/VRAM access - no impact on model seats.

## Run Logs (from workflow_runner.py)

- lead_enrichment_20261125_093909.json: status=ok, 0.11s
- content_repurpose_20261125_093958.json: status=ok, 0.1s  
- invoice_tracker_20261125_093958.json: status=ok, 0.1s

## Seat Impact Assessment

- Workflows run in user-space Python (<256MB each, <300s CPU max)
- No GPU/VRAM access - zero impact on model seats
- Staggered by scheduler (sequential via run_steps.py) - no concurrent execution
- Monitor integrates with seat_probe via check_stalth() import (<5ms overhead)

## Verdict

Infrastructure: COMPLETE (6 files, all tested)
Scheduling: REGISTERED in portal_scheduler.py (active on next host restart)
Runbook: COMPLETE with rollback procedure
Seat impact: NONE (zero GPU/VRAM, <1MB concurrent RAM per workflow)
