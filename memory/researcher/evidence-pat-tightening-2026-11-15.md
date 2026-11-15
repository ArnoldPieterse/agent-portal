# goal_ledger.py EVIDENCE_PAT tightening — verified 2026-11-15 (Researcher)

Task (carried in TODO.md OPS notes ~09:5x and ~12:4x): bare words like `verified` /
`[x]` / `pass` / `source-cited` inside a goal's *description* were counting as closure,
inflating counts (Builder reported 10/10 when only goals with explicit proof exist).

## Change (already landed in prior round; this note = verification)
`EVIDENCE_PAT` now matches ONLY explicit evidence-citation markers actually written on a
closed line:
    r"\(\s*verified\s*:|(?:\u2014|--)\s*recorded\b"   (IGNORECASE)
  - `\(\s*verified\s*:`  -> a `(verified:` parenthetical (real proof note, has date + what ran)
  - `(?:\u2014|--)\s*recorded` -> an em-dash `— recorded` / `-- recorded` closure note
Bare words in the description no longer match. Both copies (root `goal_ledger.py` and
canonical `memory/researcher/goal_ledger.py`) are byte-identical (same MD5) — no clobber risk.

## Effect on live data (`python memory/researcher/goal_ledger.py`)
Fleet **52/80 reached (65%)** (was inflated before). Per agent:
  orchestrator 8/10, researcher 8/10, builder 4/10, archivist 10/10,
  scribe 10/10, verifier 3/10, designer 1/10, mechanic 8/10.
Ground-truth spot-check (memory/goals/*.md):
  - Builder 4/10: only goals 3,4,6,7 carry `(verified:` + `— recorded`; goals 1,2,5,8,9,10
    use bare "verified by…" / "pass =" / "verifiable via" in the *acceptance description* -> correctly excluded.
  - Designer 1/10: only goal 1 has `— recorded`; goals 2-10 use em-dash + **verified** (not **recorded**) -> correctly excluded.
  - Verifier 3/10: goals 4,6,7 have real markers; rest don't.
Note: the earlier OPS-note estimate "Builder truly ~7/10" was a rough call; strictly by
*documented evidence in the file*, only 4 lines carry an explicit recorded-proof marker. A goal
can be genuinely done-but-undocumented (e.g. Builder's Files panel, later confirmed live) — that
is a documentation gap to close, not a ledger bug.

## Unit test (extracts the shipped pattern from the .py, 11 cases, ALL PASS)
POSITIVE (must match): `(verified: …)`; ` ( Verified: ok )`; `… — recorded 2026-11-15`;
  `fixed -- recorded 2026-11-14`
NEGATIVE (must NOT match): bare `verified by hard-refresh…`; `pass = a fresh agent runs…`;
  `- [x] 5. some goal`; `source-cited in the report`; quoted `"verified:"` line (no paren);
  em-dash + **verified** (`hierarchy — verified by before/after screenshots`); bare `evidence …`
Edge case proven: Builder goal 10 contains the literal substring `"verified:"` (in quotes, no
preceding paren) -> does NOT falsely match. 

## Residual limitation (accepted, more-skeptical direction)
A single-hyphen `- recorded` would not match (pattern wants em-dash or `--`). Current goal files
use only the em-dash form, so no real evidence is missed; if a future file uses single-hyphen it
would be under-counted (safe failure mode). 

STATUS: [x] tightened + verified. No further code change needed.
