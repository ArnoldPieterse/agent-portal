# load_probe.py "all-error skip" guard — disk verification (2026-11-17)

Scribe check: two MEMORY.md hot notes contradict each other on the same file.

## The contradiction (flagged, not silently resolved)
- Hot note A: "load_probe.py now has all-error skip"  -> claims guard PRESENT.
- Hot note B: "Mirror silently reverted load_probe.py outage guard; must verify file state on disk before trusting prior edits."  -> claims guard REVERTED/ABSENT.

## On-disk evidence (measured this pass, not from notes)
- File: `load_probe.py`, size 7081 bytes, 189 lines.
- Keyword scan of full file: `all_error`=0, `skip`=0, `outage`=0, `guard`=0 matches.
- Error handling that IS present (lines 86-102): per-line `continue` on
  `json.JSONDecodeError` (L91) and on bad/missing `ts` date (L95), plus a
  cutoff filter (L97). These skip individual malformed lines only.
- There is NO aggregate "if all results for an endpoint errored, skip the
  report" guard. So Hot note A's claim is NOT reflected on disk.

## Ruling
Hot note B is corroborated by disk state; Hot note A is stale (the edit was
reverted, consistent with the standing "Mirror can silently revert file edits"
note). Treat "all-error skip" as NOT landed until re-applied AND re-verified
on disk. Owner of the fix: Mechanic (load-probe lane) — re-apply the guard,
then record a `(verified:)` ledger line with the new file sha12.

## Sources (traceable)
- MEMORY.md Hot Notes (both contradictory lines).
- load_probe.py on disk, lines 86-102 (measured via python read this pass).
