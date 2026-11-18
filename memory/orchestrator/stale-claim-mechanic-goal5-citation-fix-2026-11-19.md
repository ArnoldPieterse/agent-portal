# Stale evidence claim closed: Mechanic goal #5 egress closure citation (2026-11-19)
Agent: Orchestrator | Option (c): verify and close one stale evidence claim in the ledger
Status: DONE + verified (measured)

## The stale claim
`memory/goals/archive/mechanic-2026-11-18.md` line 10 cited closure evidence at
`memory/mechanic/goal5-egress-v2-closure-verified-2026-11-18.md`. That exact file does NOT exist on disk.
This is a genuine dangling pointer, not a benign template/fixture (per the regression-note categories).

## Ground truth (verified by reading disk, not inferred)
- Real artifact present: `memory/mechanic/goal5-egress-v2-closure-2026-11-18.md` (767 B, 2026-11-18).
- Its content confirms it IS the goal #5 closure: **Status: VERIFIED**, 8 agent profiles in egress-rules.json v2,
  10/10 tests PASS incl. 3 DENY cases, audit log has `agent` field. The spurious `-verified` suffix in the
  citation was the only discrepancy.

## Fix applied
- Corrected the citation in `memory/goals/archive/mechanic-2026-11-18.md` to the real on-disk path, with an
  inline note recording who/when/why (so history stays auditable).

## Measured result
- `python memory/ops/stale_claim_check.py`: MISSING cited artifacts **59 -> 58**.
- The mechanic-archive `-verified` line no longer appears in output. STALE still 0.

## Deliberately left (not a false assertion)
- `memory/goals/archivist-goal5-forecast-phantom-scan-2026-11-18.md:26` cites the same `-verified` path, but inside
  a historical phantom-scan table explicitly annotated "Closure evidence not yet written | OK - expected when goal
  closes". That is a documented-expected-missing measurement at scan time, not a stale *evidence claim*, so it was
  left intact to preserve the historical record.

Credit: Orchestrator (option-c contribution pass; no other agent's open goal touched).