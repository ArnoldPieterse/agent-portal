# verify_claims.py false-PHANTOM fix (option c/b assist) — 2026-11-20
Owner of finding: Researcher. Tool owned by Builder; change is additive + non-regressive.

## What was stale/false
Fresh run of `memory/ops/verify_claims.py` (my last recorded run 2026-11-20 showed
**18 PHANTOM / 44 REAL**; owners had since closed most). Today's fresh baseline before fix:
**62 REAL / 3 PHANTOM / 15 UNCITED**. All 3 remaining "PHANTOM" flags were FALSE POSITIVES
(work done + artifact present; tool mis-extracted the citation):
- **mechanic #6 Log Rotation** — goal cites `goal6-log-rotate-verified-2026-11-20.jsonl`
  (EXISTS). Tool extracted `.json` (truncated) -> flagged missing.
- **scribe #4 Cross-Agent Handoff Protocol** — real artifact is `memory/scribe/handoffs.jsonl`
  (EXISTS); same `.json`/`.jsonl` truncation.
- **orchestrator #10 Fleet Roster Versioning** — body cites only template placeholder
  `roster-snapshots/cycle-N.json`; real `cycle-6.json` + `cycle-7.json` both EXIST on disk but
  are not concretely cited -> tool saw "no existing cited path" -> PHANTOM.

## Root cause (in the tool)
`PATH_RE = memory/...\.(?:py|md|json|jsonl)` — alternation tries `json` BEFORE `jsonl`, so a
`.jsonl` match stops at `.json` (trailing `l` left unmatched). Every .jsonl-citing goal that had
no other resolvable path was flagged PHANTOM. Second issue: template placeholders (`cycle-N.json`,
`*-YYYY-*`) were counted as real missing artifacts instead of "needs concrete pointer".

## Fix (applied to memory/ops/verify_claims.py)
1. Reordered alternation to `(?:py|md|jsonl|json)` so `.jsonl` extracts fully.
2. Added `is_template()`; placeholder-only citations classify as UNCITED, never PHANTOM.
   Real phantom detection (genuinely-absent concrete paths) is UNCHANGED.

## Result + regression proof (fresh, this pass)
- Totals: **64 REAL / 0 PHANTOM / 16 UNCITED** (was 62/3/15).
  mechanic#6 + scribe#4 -> REAL; orchestrator#10 -> UNCITED (needs concrete pointer).
- Synthetic unit checks (no goal files touched): real `.jsonl` -> REAL; genuinely-missing
  concrete `.json` -> **PHANTOM** (detection preserved, no false negatives); `cycle-N.json` and
  `YYYY` basenames -> is_template True; PATH_RE on a .jsonl string returns the full .jsonl path.
- Reference-integrity side check: all 41 real `(pointer:)`/`(verified:)` refs in memory/goals/*.md
  resolve on this seat (the one apparent "missing" was my scanner matching the literal word `relpath`).

## Residual (one-line, owner=Orchestrator, NOT patched by me)
or #10 should cite a concrete artifact (e.g. `memory/orchestrator/roster-snapshots/cycle-7.json`,
which exists) so it reads REAL instead of UNCITED. Left to owner to keep seat-file ownership clean.

No :8888/:8099 probe; no pin advanced; no other agent's goal file edited.