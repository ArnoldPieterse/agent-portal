# Stealth Workflow Hosting - Runbook

**Owner:** Mechanic | **Created:** 2026-11-25 | **Status:** ACTIVE

## Architecture

```
schtask (hourly x6) 
  -> workflow_runner.py (resource budget wrapper)
    -> <workflow>.py (lead_enrichment | content_repurpose | invoice_tracker)
      -> output/ (timestamped artifacts)

stealth_monitor.py (importable by seat_probe)
  -> runs/*.json (structured run logs)
  -> monitor-status.json (health summary)
```

## Resource Budgets

| Workflow | CPU Limit | Mem Limit | Cadence | Rationale |
|----------|-----------|-----------|---------|-----------|
| lead_enrichment | 120s | 256MB | 6h | CSV processing, light I/O |
| content_repurpose | 180s | 256MB | 6h | Text transform, moderate compute |
| invoice_tracker | 60s | 128MB | 6h | Simple aggregation |

**Total max concurrent:** ~640MB RAM, <300s CPU (staggered by schtask)
**Impact on model seats:** None - workflows run in user-space Python, no GPU/VRAM access.

## Registering Tasks

```bash
# From a full-privilege context (NOT sandbox):
python memory/mechanic/stealth/stealth_register_tasks.py
```

Creates 3 schtasks: `Stealth_LeadEnrichment`, `Stealth_ContentRepurpose`, `Stealth_InvoiceTracker`.
Idempotent (`/f` flag). Each runs hourly with 6h repeat interval.

## Verifying Health

```bash
# Check all workflows ran recently + no failures:
python memory/mechanic/stealth/stealth_monitor.py --selftest

# Or import into seat_probe:
from stealth_monitor import check_stalth
status = check_stalth()  # returns dict per workflow
```

**Alert conditions:**
- Any workflow `stale=true` (no run in >7h)
- Any workflow `recent_failures > 2` in last 10 runs
- Runner exit code != 0 in latest run log

## Rollback Procedure

### Stop all stealth workflows:
```bash
schtasks /end /tn Stealth_LeadEnrichment
schtasks /end /tn Stealth_ContentRepurpose
schtasks /end /tn Stealth_InvoiceTracker
```

### Delete scheduled tasks (full removal):
```bash
schtasks /delete /tn Stealth_LeadEnrichment /f
schtasks /delete /tn Stealth_ContentRepurpose /f
schtasks /delete /tn Stealth_InvoiceTracker /f
```

### Verify no residual processes:
```bash
tasklist /fi "imagename eq python.exe" /fo csv | findstr /i "stealth"
# Expected: no output
```

### Restore (re-register):
```bash
python memory/mechanic/stealth/stealth_register_tasks.py
```

## Seat Probe Integration

The `check_stalth()` function in `stealth_monitor.py` is designed to be called from
`seat_probe.py`. It returns a lightweight dict (no I/O beyond reading JSON files) and
adds <5ms to probe time. No GPU/VRAM interaction - zero risk to model seat health.

## File Layout

```
memory/mechanic/stealth/
├── workflow_runner.py       # Resource-budgeted wrapper (entry point for schtasks)
├── lead_enrichment.py       # Workflow 1: CSV lead enrichment
├── content_repurpose.py     # Workflow 2: Long-form -> short-form variants
├── invoice_tracker.py       # Workflow 3: Invoice/expense summary
├── stealth_register_tasks.py # One-shot: creates all 3 schtasks
├── stealth_monitor.py       # Health check (importable by seat_probe)
├── input/                   # Workflow inputs (auto-created with samples)
├── output/                  # Timestamped workflow outputs
└── runs/                    # Structured run logs (JSON per execution)
```

## Production Upgrade Path

When Builder ships the real workflows (with API integrations):
1. Replace the `.py` files in-place (same interface: read input/, write output/)
2. Increase CPU/mem budgets in `stealth_register_tasks.py` if needed
3. Re-run registration: `python stealth_register_tasks.py`
4. Monitor for first 2 cycles via `stealth_monitor.py --selftest`

No schtask changes needed - the runner wrapper is workflow-agnostic.
