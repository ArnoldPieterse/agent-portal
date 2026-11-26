# Forge Goal #7 Evidence: Seat-Sizing Decision Audit — 2026-11-26

## What ran
`python memory/forge/seat_sizing_audit.py --selftest` (exit 0)
`python memory/forge/seat_sizing_audit.py` (exit 0, real data)

## Result: PASS

### Selftest
Synthetic 4-agent scenario verifies audit logic: RETIRE with redundancy=0.85 correctly classified as CORRECT; SCALE/MAINTAIN with insufficient temporal data correctly classified as N/A.

### Real Data Audit
- **14 agents audited** (all seats in seat-sizing.json)
- **14/14 decidable** (autoloop.jsonl has >=10 entries per agent after case-insensitive match fix)
- **Overall correctness: 100%** — all pass rates stable across recent vs historical halves
- SCALE agents (8): no regression detected → recommendations valid
- MAINTAIN agents (6): stability confirmed → recommendations valid

### Bug found + fixed
Agent names in autoloop.jsonl are capitalized (`"Archivist"`) but seat-sizing.json uses lowercase (`"archivist"`). Fixed with case-insensitive matching in `compute_pass_rate_trend()`.

## Artifacts
- Script: `memory/forge/seat_sizing_audit.py`
- JSON report: `memory/forge/seat_sizing_audit_last.json`
- Markdown report: `memory/forge/seat-sizing-audit-report.md`

## Verification command
```
python memory/forge/seat_sizing_audit.py --selftest   # PASS (exit 0)
python memory/forge/seat_sizing_audit.py              # 14/14, 100% correct (exit 0)
```
