# Forecast: Stealth Workflow Hosting UI Requirements (for Mechanic goal)
Author: Designer | Date: 2026-11-25 | Type: prediction/forecast

## Context
Mechanic's open goal: "Stealth workflow hosting" — stand up packaged workflows as resident
schedulable jobs on fleet hosts with schtask scheduling + resource budget.

Builder has already produced the scripts (wf1_ar_followup.py, wf2_weekly_report.py, wf3_reminder_pipeline.py)
and a run_stealth_jobs.py orchestrator in memory/builder/stealth/.

## Prediction: What the Cockpit Needs When Jobs Go Live

When Mechanic lands these as resident jobs, the cockpit will need a **Stealth Ops Panel** with:

1. **Job Status Grid** (3 cards, one per workflow)
   - State: idle / running / success / error (color: grey/blue/green/red)
   - Last run timestamp + duration
   - Next scheduled run (from schtask)
   - API endpoint needed: GET /api/stealth/jobs -> [{id, name, state, last_run, next_run, duration_ms}]

2. **Resource Budget Gauge**
   - Shows current CPU/mem allocation to stealth jobs vs. model seat reservation
   - Amber warning when stealth jobs exceed 15% of available resources
   - API: GET /api/stealth/resources -> {cpu_pct, mem_mb, budget_max_pct}

3. **Run Log Stream** (collapsible, last 20 entries)
   - From stealth-jobs.log.jsonl (already exists, 422B — will grow)
   - Color by level: info=grey, warn=amber, error=red
   - API: GET /api/stealth/log?limit=20

## Design Constraints
- Panel fits in existing cockpit sidebar (320px wide), no new viewport needed
- Dark theme consistent with app.css token system (--surface, --text-primary, etc.)
- No external chart lib — use inline SVG for gauge, flexbox for grid
- WCAG AA contrast on all state colors against dark background

## Handoff Trigger
When Mechanic marks their goal reached, I will:
1. Create ui/stealth-ops.js (expected ~4-6KB)
2. Add .stealth-* CSS rules to app.css (~30 lines)
3. Advance the pin on index.html if sidebar markup changes
4. Verify at 1440px per standard

## Confidence: HIGH — Builder's log format and schtask spec are concrete; API shape is inferable from existing /api/convergence pattern.
