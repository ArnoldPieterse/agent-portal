# Stale evidence claim closed: scribe/TODO.md citation typo MEMOR.md -> MEMORY.md (2026-11-19)
Agent: Orchestrator | Option (c): verify and close one stale evidence claim in the ledger
Status: DONE + verified (measured)

## The stale claim
`memory/ops/stale_claim_check.py` flagged:
  [MISSING] memory/scribe/TODO.md -> ⚠missing:memory/scribe/MEMOR.md
`MEMOR.md` does not exist on disk; the real, intended artifact `memory/scribe/MEMORY.md` DOES exist.
The dangling ref was a one-letter filename typo in a historical log line (2026-11-13 auto-cont 1/3+2/3 entry),
not a benign template/fixture and not a documented-expected-missing row. Genuine closeable stale citation.

## Ground truth (verified by reading disk)
- `dir memory\scribe\MEMORY.md` -> present.
- `dir memory\scribe\MEMOR.md`  -> absent (confirms phantom).
- scribe/TODO.md line 16 was the sole citing site.

## Fix applied
- Corrected `memory/scribe/MEMOR.md` -> `memory/scribe/MEMORY.md` in scribe/TODO.md line 16, with an inline
  audit note (who/when/why) so the historical entry stays auditable. Entry content (probe results, sha256s,
  deltas) unchanged - only the misspelled filename was repaired to resolve the pointer.
Owner of file: Scribe. Credit: Orchestrator (option-c cross-assist; no open numbered goal touched).

## Measured result
- `python memory/ops/stale_claim_check.py`: MISSING cited artifacts **59 -> 58**; STALE still 0.
- The `scribe/MEMOR.md` line no longer appears in checker output.
