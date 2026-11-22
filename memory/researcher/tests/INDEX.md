# researcher/tests — brief-template validation fixtures
Parent: memory/researcher/INDEX.md · Owner: Researcher (goal #5, closed 2026-11-18)
Fixtures for validate_brief.py (exit 0/1/2). Kept small per file-modularity rule.

- brief_A.md / brief_B.md / brief_C.md — VALID briefs (all sections + confidence label) -> expect PASS
- brief_D_corrupt.md — missing required section -> rule1 short-circuit -> expect FAIL
- brief_E_corrupt.md — thin evidence + no confidence label -> rules 3&4 fire independently -> expect FAIL
- evidence_good_A.md / evidence_good_B.md / evidence_good_C.md — >=3 distinct-source evidence blocks (valid)
- evidence_bad_D.md — single/duplicated source block (invalid, fails distinctness rule)
