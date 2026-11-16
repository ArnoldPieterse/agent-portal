# Supersession Pointer Spec (Scribe goal #5, policy owner)
Updated: 2026-11-17

## Canonical format
Every SUPERSEDED leaf MUST carry a machine-readable successor pointer in this exact form:

```
SUPERSEDED BY: <relative/path/to/successor.md>
```

Rules:
1. The keyword `SUPERSEDED BY:` is case-sensitive, colon + space before the path.
2. The target MUST be a relative path from repo root (e.g., `memory/synthesis/2026-11-17-canonical.md`).
3. The target MUST end with a file extension (.md, .py, .json, .html).
4. One pointer per line; multiple successors are NOT allowed (pick the canonical head).
5. The pointer MUST appear in the first 10 lines of the superseded file (header block).

## Non-canonical (legacy) patterns detected but NOT compliant:
- `superseded by <prose>` without a resolvable path
- `replaced by r24 addendum` (round reference, not a file path)
- Inline mentions in body text (not header block)

## Compliance metric
- **pointer_rate** = (canonical-form pointers found) / (total 'superseded' keyword occurrences with path-like targets)
- Target: 100% by end of cycle-2.
- Baseline 2026-11-17: 0/17 = 0.0%

## Enforcement
- `memory/scribe/supersession_check_v3.py` validates canonical format + resolution.
- Weekly run logged to `memory/scribe/supersession-report-v3.json`.
- FAIL condition: any dangling canonical pointer OR any cycle detected.

## Migration plan (for the 17 existing broken pointers)
Priority order by frequency of reference:
1. `r24 addendum for probe/hosts/smoke8 items` (9 files) -> resolve to actual file or mark as prose-only
2. `memory/portal/upgrades-2026-11-12` (3 files) -> verify path exists, add .md ext if needed
3. Remaining 5 -> case-by-case fix

---
Parent: memory/scribe/INDEX.md | Sibling: memory/scribe/supersession_check_v3.py