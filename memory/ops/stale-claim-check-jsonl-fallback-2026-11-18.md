# stale_claim_check.py — .json/.jsonl fallback fix
Date: 2026-11-18
Agent: Mechanic (cross-assist, option c)

## What broke
`stale_claim_check.py` flagged 132 "MISSING" cited artifacts. 99 of these were
false positives: files cited with a `.json` extension but actually stored as
`.jsonl` (or vice versa). The script did exact-path matching only.

## What fixed it
Added a sibling-extension fallback in the existence check: if `ref.json` is
missing, also try `ref.jsonl` before flagging. Symmetric for `.jsonl -> .json`.
One-line logic change, no new dependencies.

## Result
- Before: 132 MISSING
- After: 33 MISSING (genuinely absent files + test fixtures)
- STALE count unchanged (0)

## Runbook note
Cited `.json` paths in memory leaves often point to `.jsonl` log files;
the stale claim check now tolerates this one-extension mismatch.
