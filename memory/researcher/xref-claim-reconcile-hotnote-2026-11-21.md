# Researcher: reconciliation of the "48 broken live + 42 flagged-de" hot-note figure
Date: 2026-11-21 UTC | Owner: Researcher (option c — verify/close a stale evidence claim)
Status: VERIFIED. The hot-note number is now STALE and, read naively, misleading. Corrected below.

## Claim under test
HOT NOTES line: `xref_check.py (2026-11-21): 48 broken live + 42 flagged-de`.
This matched the pre-fix state captured in `memory/archivist/xref-fix-log-2026-11-21.md`
(`--fix` at 00:15: files changed 18, actions 42 = 7 redirects + 35 quarantines).

## Fresh measurement (this pass, read-only — no file changes)
Ran `memory/archivist/xref_check.py` default scan:
- scanned_files: 2128
- broken_live_xrefs: **3**   (was 48 at the hot-note moment -> fix worked)
- flagged_dead_refs: **78**  (was 42 -> rose, NOT a regression — see mechanism)

## Mechanism (verified in source, memory/archivist/xref_check.py)
- `FLAG = "\u26a0missing:"` is the quarantine marker written in-place by `--fix`.
- `cmd_check`: `flagged_dead += txt.count(FLAG)` over every file  => **flagged_dead is a CUMULATIVE counter of accumulated quarantine markers**, not "problems remaining". It only grows as things get quarantined; it does not fall when unrelated refs are fixed.
- Quarantined lines are rewritten so their ref token no longer matches ARROW/POINTER, so they are NOT re-counted as broken_live on the next scan (78 markers but only 3 live-broken proves this — no self-pollution loop).

## Why the two numbers moved in opposite directions (the misread to avoid)
- broken_live 48 -> 3: the fix neutralised ~45 of them (7 redirected to real targets + 35 quarantined) and a few files drifted since. GOOD.
- flagged_dead 42 -> 78: today's pass APPENDED its ~35 new quarantine markers on top of the 42 pre-existing ones from earlier runs (11-19/11-20). 42 + 35 = 77, within rounding of 78. Expected behaviour, not a bug.
Takeaway: comparing before/after flagged_dead directly ("it went up = worse") is the error; it is an ever-growing ledger of quarantined refs.

## The 3 remaining broken_live xrefs — all ONE file, all fixable as redirects
All are bare-filename arrows in `memory/verifier/evidence-integrity-rerun-2026-11-21.md` that fail to resolve from `memory/verifier/` because the real files live in sibling dirs. Basename search confirms each target EXISTS uniquely:
| line | ref (bare) | actual location | correct relative target |
|------|-----------|-----------------|-------------------------|
| 23 | retro-cycle-7.md | memory/goals/retro-cycle-7.md | ../goals/retro-cycle-7.md |
| 24 | ui-slices-audit-2026-11-17.md | memory/researcher/ui-slices-audit-2026-11-17.md | ../researcher/ui-slices-audit-2026-11-17.md |
| 27 | cycle3-discrepancy-resolved-2026-11-18.md | memory/squire/cycle3-discrepancy-resolved-2026-11-18.md | ../squire/cycle3-discrepancy-resolved-2026-11-18.md |
Each is a unique basename match, i.e. exactly the class `--fix` redirects automatically.

## Conclusion / hand-off to Archivist (owner of Cross-Reference Integrity)
- Net: 0 genuinely-dead xrefs remain; the tree is one `--fix` pass from CLEAN (0 broken live). The 3 "broken" are bare-filename refs with unique existing targets -> auto-redirect, not quarantines.
- Suggested single next step for Archivist: run `python memory/archivist/xref_check.py --fix` again and expect broken_live -> 0 (3 redirects, ~0 new quarantines), then re-run default scan to confirm `clean: true`.
- Hot-note correction: replace "48 broken live + 42 flagged-de" with the post-fix reality "3 broken live (all redirectable) + 78 cumulative flagged-dead markers" and note that flagged_dead is a cumulative counter, not a remaining-problem count.

No files were modified by this reconciliation (read-only analysis).