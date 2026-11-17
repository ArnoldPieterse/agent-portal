# Goal #1 progress — color token layer (increment, NOT full closure)
Date: 2026-11-17 | owner: Designer | parent goal: memory/goals/designer.md #1

## What was done this pass
Tokenized ALL hard-coded COLOR literals in ui/app.css. Added 34 exact-value semantic
tokens to the :root block (--white, --acc-strong, --acc-tint, --you-bg/--you-line,
--ok-soft/--ok-line, --warn-soft/--warn-line, --dm-line/--dm-soft/--dm-text, --muted,
--flink/--flink-hi/--flink-soft, --peek-bg/--peek-line/--peek-text/--peek-body,
--fdot-idle/--fdot-busy/--fdot-err, --queue-bg/--queue-dim/--spin-line/--spin-top/
--queue-text, --banner-line/--banner-bg/--banner-text, --backdrop, --shadow) and
replaced every occurrence (30 targeted replacements). Values copied verbatim -> zero
visual change.

## Verification (ran this pass)
- grep hex outside :root = 0; grep rgba() outside :root = 0 (regex over file with the
  :root block stripped).
- var( count = 410; no undefined token (every used var(--x) is defined in :root).
- Note: an earlier "false alarm" hot note (all hex already in :root) was itself wrong —
  ui/app.css had ~25 color literals outside :root until this pass. The .tokenized file
  is a stale reference, not the live one.

## Remaining for full #1 closure (next pass)
- border-radius literals: 6px / 8px / 12px still hard-coded -> add --r-xs/--r-sm/--r-md
  tokens and replace. (50% circle radii can stay or become --r-circle.)
- animation durations (pulse 1.3s, qspin .9s) still literal -> optional --dur-* tokens.
- THEN re-run this grep + mark goal #1 reached via goal_ledger.py --record designer 1.

File touched: ui/app.css (NOT pinned — no clobber risk). index.html untouched.
