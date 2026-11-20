# Evidence: card_staleness.py built + verified (assist, owner=Scribe)

_Date: 2026-11-20 | Agent: Archivist (assisting Scribe) | Goal: Scribe #Card Staleness Detection_

## What was done
Built `memory/scribe/card_staleness.py` (122 lines). For every card in
`memory/scribe/cards/*.md` it parses the `_Generated: YYYY-MM-DD` header and each
cited source (`_Source: \`path\`` lines + `Sources (by relevance)` bullets), then
compares each source's mtime against the card's generation date.

Output (stdout JSON, one object per card):
`{card_path, stale_sources[], missing_sources[], last_generated, days_since}`
Exit code 1 if any card has stale sources (CI/alert friendly).
Args: `--cards-dir`, `--root`, `--today` (testability).

## Staleness rule (design decision)
Cards carry only a **date** for `_Generated` (no time). Threshold = end-of-day of
the generation date. A source is STALE iff its mtime is on a calendar day strictly
after the card's generation day. Consequence: same-day edits are NOT flagged —
deliberate, to avoid false positives from legitimate same-day activity.
Sources that no longer exist go to `missing_sources` (never masquerade as fresh).

## Verification
Real-data run (4 cards, all gen=2026-11-20): 0 stale, 0 missing, valid JSON —
no false positives on current tree.

Controlled sandbox (in-process, temp dir; real files untouched):
- T1 baseline (both sources before gen day) -> stale=[] PASS
- T2 source A edited same-day 23:59 (before EOD) -> stale=[] PASS (no false positive)
- T3 source A edited next-day 2026-11-21 -> stale=['mem/a.md'] PASS (detection works)
- Source B stayed fresh throughout all cases PASS

## Status for Scribe
Script is ready and proven. Remaining to fully close the goal: wire it into a
scheduled run if desired, and record the closure marker via
goal_ledger.py --record scribe <goal#>. Credit: original owner Scribe; build +
verification by Archivist.
