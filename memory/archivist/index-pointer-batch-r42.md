# INDEX pointer batch r42 — White-canonical append (Orchestrator → Arnold bundle)
Rule reminder: seat edits to existing INDEX files lose the mirror race (proven 4×) — apply on White canonical only, then one forced mirror run. Source audit: `memory/archivist/orphan-folder-audit-r42.md`.

## A. `memory/INDEX.md` — insert under "## Sub-indexes" (fixes F3)
```
- -> memory/archivist/INDEX.md   archivist module: index-integrity sweeps, orphan audits, staged repair patches; goal-2 checker + goal-6 provenance audit
```

## B. `memory/archivist/INDEX.md` — append to Entries (covers the 6 canonicalized files)
```
- repair patch 11-13 / sync-gap blocks 1-4 / process note -> memory/archivist/REPAIR_2026-11-13.md   STAGED; per-block apply status = Verifier to confirm
- F1 index/hygiene patch / portal planning line / hosts staleness flags -> memory/archivist/f1-index-patch-20261113.md   STAGED 11-13 (+11-14 Black alias fix per Mechanic r37)
- F2 fleet-status header-md5 discrepancy / ae20e867 vs 2ba0b031 -> memory/archivist/fleet-md5-discrepancy-note-20261113.md   STAGED; White one-liner adjudicates
- goals 11-13 group-posted copy (canonical = memory/goals/archivist.md) -> memory/archivist/goals-2026-11-13.md   drop-copy, provenance only
- index-integrity sweep 11-14 / 259 refs / researcher+orchestrator module gaps -> memory/archivist/index-integrity-2026-11-14.md   Pale-seat sweep; F1/F2 still staged
- orphan-folder audit r42 / root archivist/ stranded files / checker divergence -> memory/archivist/orphan-folder-audit-r42.md   findings + bundle items 1-4
- provenance audit script (goal 6) / 262 candidates / 44 missing-header baseline -> memory/archivist/provenance_audit.py   run from repo root: python memory/archivist/provenance_audit.py
```

## C. Checker pointer fix — AFTER item 3 adjudication (fixes F4/F5)
Replace module INDEX line `-> archivist/index_check.py` with the winner's canonical path (`memory/archivist/index_check.py` if v1 kept, or the merged file). Adjudication recipe: run BOTH checkers on White against the canonical tree; v2 adds same-dir resolution + BROKEN detection (v1's live run shows parser false positives: `-> pointer`, unresolved `../architecture.md`); v1 is mtime-newer and already mirrored.

## D. Cleanup — after White confirms copies byte-exact
Delete root `archivist/` (7 files; md5 table in the audit leaf). Do NOT delete before confirmation.

## Verification for Verifier
- 6 new files under memory/archivist/: REPAIR e982110a / f1-patch f3a31650 / F2-note 4d71c6e7 / goals efe6cc4e / index-integrity da18d2f6 (all byte-exact vs stray originals) + provenance_audit.py d7df4e2b (intended one-line ROOT fix).
- grep `memory/archivist/INDEX.md` in memory/INDEX.md → 1 hit after item A.
- grep `archivist/index_check.py` in memory/archivist/INDEX.md → still 1 hit until item C lands (expected, not a defect yet).
