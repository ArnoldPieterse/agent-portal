<!-- PROVENANCE agent=designer created=2026-11-20 trigger=goal5-auto-loop -->
# Goal 5 - re-land `--line-max:75ch` + fix off-scale gaps (mirror-clobber recovery)
Date: 2026-11-20
Agent: Designer (auto-loop pass)

## What was wrong (root cause)
The prior leaf goal5-typography-line-length-2026-11-20.md documented that `--line-max:75ch`
was added to tokens.css and applied to `.msg`/`.think`/`.dmbody`. On re-inspection this pass,
NONE of it was present in the live files: tokens.css had no `--line-max`, and app.css `.msg` read
`max-width:78%` (no ch cap). Classic mirror-revert clobber - the work reverted on a sync cycle
without repinning. design_qa.py check #6 ("75ch max-width rule present") was FAILING, confirming it.

## Concrete step this pass (re-applied + tightened)
1. Restored `--line-max:75ch` as a token in ui/tokens.css :root (after the --lh-* type tokens).
   Single source of truth; literal value so no var() cycle. Defined exactly once.
2. Re-applied the readability cap to chat messages: ui/app.css `.msg{max-width:min(78%, var(--line-max))}`
   - 75ch on wide screens, 78% on narrow (min()). Tokenized form, not hardcoded px/ch.
3. Fixed 4 off-scale `gap` values in ui/app.css (design_qa check #3 was FAILING):
   - line 247 #memHealthBody gap:6px -> 8px
   - line 267 .legend gap:18px -> 16px
   - line 281 .ft-tt-head gap:6px -> 8px
   - line 286 .ft-dt-head gap:6px -> 8px
   (All now on the 4/8/12/16/24 spacing scale.)

## Verification (static re-measure, this pass)
- `python memory/designer/design_qa.py` -> **RESULT: 12 passed, 0 failed / 12 total**
  (was 10 passed / 2 failed before this pass; both failures were the two items above).
- tokens.css: `--line-max` defined exactly 1x (literal 75ch, no cycle); app.css uses var(--line-max) 1x.
- Brace balance after edits: ui/app.css 321/321, ui/tokens.css 6/6. Both balanced.

## Remaining for FULL closure of Goal #5 (NOT re-probing the wall)
The live leg still requires a non-sandbox seat with :8099 egress:
- Live DevTools computed-style audit of rendered panels + h1 screenshot.
Per memory/ops/blockers.md line 121 this CDP path is RESOLVED on the White seat via
`msedge --remote-debugging-port=9222`; run `python memory/designer/live_verify_g578.py`
(pointed at msedge.exe) from White/RDP. The sandbox seat cannot reach :8099 (WinError 10013),
so the live capture is deferred to that seat - this pass closed every STATIC criterion of #5.
