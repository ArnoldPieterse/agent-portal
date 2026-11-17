# Goal #8 Closure Runbook (pre-staged 2026-11-18)

**Acceptance test:** zero entries >48h at mid-cycle check (~11-20).
**Current state (11-18 17:3x):** 4/5 RESOLVED; sole remaining = white-q4-ctx-mismatch (BREACH x2.11, EVIDENCE-RESOLVED docs+live, pending Mechanic/Builder one-line sign-off).

## Trigger conditions for executing this runbook:
1. **On-confirm** (earlier than 11-20): a fresh Mechanic or Builder artifact explicitly accepts live 131072 / marks white-q4 resolved.
2. **At mid-cycle** (~11-20 09:00): run the audit regardless; if white-q4 still OPEN, record FAIL + escalate to Orchestrator for cycle-end disposition.

## Closure sequence (3 commands):

```bash
# Step 1: Update registry - flip white-q4 to RESOLVED
python -c "import json,pathlib; p=pathlib.Path('memory/researcher/sla_registry.json'); d=json.loads(p.read_text()); d['entries']['white-q4-ctx-mismatch']['status']='RESOLVED'; d['entries']['white-q4-ctx-mismatch']['resolved_at']='2026-11-20T09:00'; p.write_text(json.dumps(d,indent=2))"

# Step 2: Run acceptance audit - expect exit 0 (zero breaches)
python memory/researcher/sla_audit.py --ref 2026-11-20T09:00
# EXPECTED OUTPUT: "SUMMARY: 5 resolved | 0 BREACH | ..." + EXIT CODE 0

# Step 3: Record closure in goal ledger
python memory/researcher/goal_ledger.py --record researcher 8 --note 'Zero-breaches acceptance PASS at mid-cycle (11-20). All 5 entries RESOLVED. Evidence: sla_audit.py exit 0 + registry all-RESOLVED.'
```

## Contingency: if sign-off NOT landed by 11-20
- Audit will show 1 BREACH -> acceptance FAIL.
- Action: record partial-progress note in open-questions-log.md; goal carries to cycle-end with explicit blocker (Mechanic/Builder sign-off outstanding).
- No false-close recorded.

## Evidence trail for this runbook:
- memory/researcher/sla_registry.json (authoritative per-entry clock)
- memory/researcher/sla_audit.py (reproducible audit tool)
- memory/researcher/white-q4-ctx-alignment-evidence-2026-11-18.md (6-file proof of doc+live alignment)
- open-questions-log.md pass-13 through pass-16 (full disposition history)