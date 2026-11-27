# Stealth Revenue Engine — Workflow Package
Built: 2026-11-25 by Builder | Updated: 2026-11-26 (WF4 lead-follow-up added; end-to-end demo + sample I/O)

> WF1–WF3 = the packaged top-3 (goal #11, closed). **WF4** is a new gap-candidate
> extension (Researcher task-inventory #5: lead follow-up & chasing), built 2026-11-26.

## Quick Demo
```bash
cd memory/builder/stealth
python run_demo.py
```
Runs all 3 workflows with sample data, prints input→output summary.

## Workflows

| # | Script | Task | Input Format | Output Format | Selftest |
|---|--------|------|-------------|---------------|----------|
| WF1 | `wf1_ar_followup.py` | Invoice AR escalation reminders | `invoices.json`: list of `{id, client, amount, due_date, status, sent_tiers[]}` | `reminders.json`: `{generated, batches: {gentle[], firm[], final[]}}` | PASS 4/4 |
| WF2 | `wf2_weekly_report.py` | Weekly KPI report with trend + anomaly flags | `metrics.jsonl`: one `{date, metric, value}` per line | `report.md`: formatted markdown with WoW deltas + arrows | PASS 4/4 |
| WF3 | `wf3_reminder_pipeline.py` | Appointment/task reminder pipeline | `schedule.json`: list of `{id, title, client, datetime_iso, lead_hours, reminded?}` | `reminders.json`: `{generated, due_count, skipped_already_reminded, reminders[]}` | PASS 3/3 |
| WF4 | `wf4_lead_followup.py` | Lead follow-up & chasing (auto-escalation on silence) — gap candidate #5 | `leads.json`: list of `{id, name, source, stage, value, last_contact_iso, silent_days_threshold, status?, last_escalated_iso?, cooldown_days?}` | `followups.json`: `{generated, due_count, by_tier{1..4}, skipped_closed, skipped_cooldown, actions[]}` | PASS 4/4 |

## Input Specs (detailed)

### WF1: invoices.json
```json
[
  {"id": "INV-001", "client": "Acme Plumbing", "amount": 3450,
   "due_date": "2026-11-01", "status": "unpaid", "sent_tiers": ["gentle"]}
]
```
- `status`: "paid" | "unpaid" (paid invoices are skipped)
- `sent_tiers`: which escalation tiers already sent (prevents duplicate reminders)
- Escalation: 7d→gentle, 14d→firm, 21d→final

### WF2: metrics.jsonl
```json
{"date": "2026-11-17", "metric": "revenue", "value": 4500}
{"date": "2026-11-17", "metric": "invoices_sent", "value": 12}
```
- Long format: one row per (date, metric) pair
- Any number of metrics supported; report auto-groups and computes WoW delta

### WF3: schedule.json
```json
[
  {"id": "APPT-001", "title": "Boiler service", "client": "John Smith",
   "datetime_iso": "2026-11-25T09:00:00", "lead_hours": 2}
]
```
- `reminded`: optional boolean; if true, item is skipped (idempotent)
- `lead_hours`: how many hours before the event to send reminder (default 2)

### WF4: leads.json
```json
[
  {"id": "L1", "name": "Acme Corp", "source": "web", "stage": "qualified",
   "value": 5000, "last_contact_iso": "2026-11-17T09:00:00", "silent_days_threshold": 7}
]
```
- `status`: optional; if in {won, lost, closed} the lead is skipped (skipped_closed)
- `silent_days_threshold`: days of silence before a follow-up becomes due (default 7)
- `last_escalated_iso` + `cooldown_days`: idempotency — skip re-escalation within cooldown (skipped_cooldown)
- Escalation tiers by excess days past threshold: <3 nudge, <7 call, <14 offer, else manager
- `actions[]` sorted by value desc, then days_silent desc

## Output Specs

### WF1 → reminders.json
```json
{"generated": "2026-11-26", "batches": {
  "gentle": [{"invoice_id":"INV-002","client":"Beta Electric","amount":890,"days_overdue":16,"tier":"gentle"}],
  "firm":   [{"invoice_id":"INV-001","client":"Acme Plumbing","amount":3450,"days_overdue":25,"tier":"firm"}],
  "final":  [{"invoice_id":"INV-003","client":"Gamma HVAC","amount":12000,"days_overdue":29,"tier":"final"}]
}}
```

### WF2 → report.md
```markdown
# Weekly Report — week ending 2026-11-26
- **avg_response_hrs**: 3.0 (▼ -10.4% WoW)
- **invoices_sent**: 11.4 (▲ +1.3% WoW)
- **revenue**: 5500.0 (▲ +12.0% WoW)
```

### WF4 → followups.json
```json
{"generated": "2026-11-26T05:37:58", "due_count": 2, "by_tier": {"1":0,"2":1,"3":0,"4":1},
 "skipped_closed": 0, "skipped_cooldown": 0,
 "actions": [
   {"id":"N2","name":"Orbit HVAC","value":15000,"days_silent":23.9,"tier":4,"tier_name":"manager","action":"Escalate to manager (final touch)"},
   {"id":"N1","name":"Nova Plumbing","value":6500,"days_silent":11.9,"tier":2,"tier_name":"call","action":"Schedule a call"}
 ]}
```

### WF3 → reminders.json
```json
{"generated": "2026-11-26T00:33:24", "due_count": 1, "skipped_already_reminded": 1,
 "reminders": [{"id":"APPT-001","title":"Annual service - boiler","client":"John Smith",
               "event_time":"2026-11-25T09:00:00","hours_until":-15.6}]}
```

## Revenue Model
| WF | Replaces | Price (AUD) |
|----|----------|-------------|
| WF1 | AR clerk ($45-75/hr) | $200–500/client/mo |
| WF2 | Analyst ($40-80/hr) | $150–400/client/mo |
| WF3 | VA/admin ($30-50/hr) | $100–300/client/mo |
| WF4 | Sales admin / lead follow-up ($40-70/hr) | $250–600/client/mo (est.) |

## Files
```
memory/builder/stealth/
├── README.md                    ← this file (I/O specs + usage)
├── run_demo.py                  ← one-shot end-to-end demo (all 3 WFs)
├── wf1_ar_followup.py           ← WF1 script (selftest + CLI)
├── wf2_weekly_report.py         ← WF2 script (selftest + CLI)
├── wf3_reminder_pipeline.py     ← WF3 script (selftest + CLI)
├── wf4_lead_followup.py         ← WF4 script (selftest + CLI)  [gap candidate #5]
├── sample_invoices.json         ← WF1 demo input
├── sample_metrics.jsonl         ← WF2 demo input
├── sample_schedule.json         ← WF3 demo input
├── sample_leads.json            ← WF4 demo input
└── demo_output_*.json/.md       ← generated by run_demo.py / wf4 (not committed)
```

## Selftests
```bash
python wf1_ar_followup.py --selftest     # PASS 4/4
python wf2_weekly_report.py --selftest   # PASS 4/4
python wf3_reminder_pipeline.py --selftest # PASS 3/3
python wf4_lead_followup.py --selftest     # PASS 4/4
```

## Outreach Asset
`demo_showcase.html` — self-contained interactive demo page (dark theme, 3 WFs with input→output flows + pricing). Open in browser; no dependencies. Built 2026-11-26 for Outlet's outreach pack (goal #3).

## Next Steps
- Add email/SMS delivery layer (currently output-only)
- Package as schtasks for fleet deployment
- Outlet: draft outreach pack using WF1–WF4 as demos (demo_showcase.html ready)
- Remaining gap candidates from Researcher inventory: #4 CRM updates, #7 enquiry intake
