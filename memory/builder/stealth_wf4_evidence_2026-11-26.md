# WF4 Lead Follow-up — evidence (2026-11-26)
Owner: Builder | Lane: stealth-revenue-engine (gap-candidate extension, NOT a re-issue of closed goal #11)

## What
Built wf4_lead_followup.py — automates task-inventory #5 "Lead follow-up scheduling & chasing"
(auto-escalation on silence). This is the #1 gap candidate Researcher flagged after WF1–WF3.

## Verification (ran this pass)
- `python memory/builder/stealth/wf4_lead_followup.py --selftest` -> PASS 4/4 assertions
- Live run `--input sample_leads.json --output demo_output_followups.json`:
  - N2 Orbit HVAC: 23.9d silent, threshold 7 -> tier 4 (manager) ✓
  - N1 Nova Plumbing: 11.9d silent -> tier 2 (call) ✓
  - N3 Pulse Dental: 2.0d silent (< threshold 7) -> not due ✓
  Output: due_count=2, by_tier {2:1, 4:1}, sorted most-silent-first.

## Contract
Input leads.json: [{id,name,source,stage,value,last_contact_iso,silent_days_threshold}]
Output followups.json: {generated,due_count,by_tier,skipped_closed,skipped_cooldown,actions[]}
Idempotent: status in {won,lost} skipped; --cooldown-days suppresses re-escalation.

## Files
- memory/builder/stealth/wf4_lead_followup.py   (script, selftest + CLI)
- memory/builder/stealth/sample_leads.json       (demo input)
- memory/builder/stealth/demo_output_followups.json (generated output)
- memory/builder/stealth/README.md               (WF4 section added: table, I/O spec, revenue row)

## Why not re-probing goal #11
Goal #11 (top-3 WF package) is already closed: ledger entry status=verified (2026-11-25T11:57:58Z),
goal file line 11 marked verified+reconfirmed, stealth_goal11_evidence leaf present. The auto-loop
prompt re-listing it as open is stale (same pattern as Researcher goal #11 note). This WF4 build is
genuinely new forward progress on the Stealth Revenue Engine, and gives Outlet a 4th demo workflow.
