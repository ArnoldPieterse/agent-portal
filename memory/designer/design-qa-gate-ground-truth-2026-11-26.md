# design_qa.py ground truth - 2026-11-26 (Designer auto-loop, option c)

## What was wrong
HOT NOTES carried THREE conflicting QA-gate numbers: "4/7", "6pass", "12/12 green".
Root cause of the confusion: `memory/designer/design_qa.py` (the 12-check gate) had a
**latent encoding bug** - every `open()` was bare (no `encoding=`), so on this host it
defaulted to cp1252 and **crashed with UnicodeDecodeError** on the first non-ASCII byte
in the CSS (0x90). It therefore produced NO verdict here, meaning any "12/12 green"
claim could not have come from this tool running on this host.

## Fix applied (real file change)
Added a UTF-8-safe `_r()` helper (`open(p, encoding="utf-8", errors="replace")`) and
replaced all 7 `open().read()` call sites in memory/designer/design_qa.py. Gate now runs
cleanly end-to-end on this host.

## Ground-truth run (2026-11-26, this host)
`python memory/designer/design_qa.py` -> **RESULT: 6 passed, 6 failed / 12 total**

PASS: 5 (reduced-motion), 7 (emptyState>=5), 8 (skeleton>=3), 9 (no external icon lib),
      10 (>=20 icons), 11 (touch targets >=44px)
FAIL (real regressions, file-level):
  1. Typography off-scale: alert-triage.css uses 10px/13px/11px (not on 5-step scale)
  2. Tokens orphaned: --fs-11 / --fs-13 / --fs-16 defined but off canonical scale
  3. Spacing: 16 off-scale gaps (3px,6px,18px...) - exceeds <=3 tolerance
  4. Interaction: 17 ad-hoc :hover rules in app.css (should live in interactions.css)
  6. Typography: 75ch max-width rule missing from CSS
  12. Visual: unknown hex in app.css not in tokens: #4caf50 #3a4a5a #4caf7d #d05656

## Discrepancy resolution
- "4/7" = STALE (older snapshot). Closed.
- "12/12 green" = NOT reproducible on this host; tool was crashing (encoding bug). Superseded.
- **Current truth = 6/12.** A regression occurred after the last genuine all-green state,
  most plausibly from newly added CSS (alert-triage.css etc.) that violates the scale.

## Handoff (who fixes what) - NOT in scope for this one-step verify
- Typography/token regressions (#1,#2): owner of design-token system goal; align
  alert-triage.css to --fs-* tokens, drop orphaned --fs-11/13/16 or add to scale deliberately.
- Spacing (#3): tighten gap values onto 4/8/12/16/24px scale.
- :hover consolidation (#4): move the 17 app.css :hover rules into interactions.css.
- 75ch rule (#6) + hex tokenization (#12): add missing max-width; replace literal hex with var().

## Verdict
Stale-claim flag RESOLVED with proof: gate is now runnable on-host and reports a single
authoritative number (6/12). Tooling defect fixed; 6 genuine design regressions surfaced
and handed off for the owning goal. This supersedes all prior conflicting QA-gate notes.
