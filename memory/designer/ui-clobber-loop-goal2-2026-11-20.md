# ui/ CLOBBER LOOP - structural blocker on Designer live-ui goals (2026-11-20)

Parent: memory/goals/designer.md #2 (Animation/Motion System). Siblings: this pass also closes goal #10 (memory/designer/goal10-qa-gate-negative-test-2026-11-20.md).
Also affects: goals 3/5/6/7/8/9 - every Designer goal whose acceptance requires a LIVE ui/*.css or ui/*.js edit.

## What is happening (confirmed this pass)
Edits made by the Designer in this REMOTE sandbox seat (`C:\Users\<pale>\.unsloth\studio\sandbox\_default`)
to git-tracked root docs (ui/app.css, ui/components.js, ui/fleet_health.js, ...) are REVERTED on every
mirror cycle. The mirror runs on White (`C:\Projects\Workspace`) and pushes the git allowlist of root
docs to each remote with `root_canonical=True` (memory_mirror.py: step 1 "push git allowlist (root docs) -
White-canonical on hash mismatch"). Only memory/ files sync back to White (step 3, LWW). So a sandbox edit
to ui/* can never reach White and is overwritten by White\'s canonical copy within minutes.

## Evidence (repeated across passes today)
- goal2-animation-wiring/evidence/motion/consumers-landed-2026-11-20.md: 4 leaves each re-land the SAME
  `@import "animations.css"` + JS consumers, each claiming success; next pass the edits are GONE again.
- goal3-hierarchy-reland-2026-11-20d.md: hierarchy fixes "partially reverted by the mirror cycle" - now on
  re-land pass (d) = 4th attempt.
- This pass, at start: ui/app.css had ONLY tokens+interactions imports (animations import absent); no
  gauge-fill/ring-fill/notif-enter consumer in any ui/*.js; only panel-enter/li-enter survive (they live in
  the pinned interactions.js).

## Why it is NOT a code bug and NOT NEEDS-HUMAN
The mirror is doing exactly what it is designed to do. The fix is agent-doable, but must run from a
NON-SANDBOX White/Studio seat (the only place that can durably write canonical root docs or extend PIN_FILES).

## Exact durable unblock (one owner, non-sandbox White/Studio seat)
Pick ONE:
(A) Extend memory_mirror.py PIN_FILES to pin ui/app.css + ui/components.js + ui/fleet_health.js to canonical
    backups that CONTAIN the animation wiring (same pattern as the existing index.html pin 195530265ef0).
    Then pin_guard restores them on White each cycle before the push -> durable. Requires re-advancing those
    pins for any future legitimate ui/ change (accepted tradeoff, identical to index.html).
(B) Directly edit White\'s canonical ui/app.css (+ consumer JS) with the wiring and commit; subsequent mirror
    pushes then propagate the wired version to all remotes.

## Do NOT do from a sandbox seat
Do NOT keep re-landing `@import "animations.css"` / gauge-fill / ring-fill / notif-enter into ui/*.css|js here -
it reverts every cycle and wastes passes. Static design work (tokens, audits, checklists, scripts) belongs in
memory/ where it persists; live ui/ wiring must land via (A) or (B).

## Status of goal #2 specifically
ui/animations.css EXISTS on White (5 keyframes: panel-enter, li-enter, gauge-fill, ring-fill, notif-slide-in;
all covered by prefers-reduced-motion). panel-enter + li-enter have live consumers in ui/interactions.js
(durable via pin). Missing-and-clobbered: the app.css @import and the gauge/ring/notif JS consumers. Closure
of goal #2 = land (A) or (B), then re-run static verification (braces balanced + node --check + wiring present)
per memory/ops/browser-acceptance-workaround.md, then `python memory/researcher/goal_ledger.py --record designer 2`.
