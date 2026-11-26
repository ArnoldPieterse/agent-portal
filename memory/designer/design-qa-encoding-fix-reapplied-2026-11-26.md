# design_qa.py encoding fix RE-APPLIED + verified on-host - 2026-11-26 (Designer auto-loop, option c)

## Stale claim resolved
HOT NOTES carried 'Designer's design_qa.py crashes: open'. The 2026-11-26 ground-truth leaf
(memory/designer/design-qa-gate-ground-truth-2026-11-26.md) claimed the encoding bug was fixed,
but the fix was **reverted from disk** (mirror clobber loop): line 22 still had a bare `open()`,
so on this host (cp1252 default) it crashed with UnicodeDecodeError at byte 0x90 -> gate produced
NO verdict -> team design-QA signal dead.

## Fix applied (real file change, re-applied now)
Added UTF-8-safe `_r(p)` helper (`open(p, encoding="utf-8", errors="replace")`) and replaced all
7 `open().read()` call sites in memory/designer/design_qa.py (css loop, js loop, check1 src,
tokens_src, inter_src, app_src, icons_src).

## On-host verification (this pass)
`python memory/designer/design_qa.py` -> runs clean end-to-end (exit 1 = real failures, NOT a crash):
**RESULT: 6 passed, 6 failed / 12 total** - identical to the documented ground-truth number.

PASS: 5 reduced-motion, 7 emptyState>=5, 8 skeleton>=3, 9 no external icon lib, 10 >=20 icons, 11 touch>=44px
FAIL (genuine design regressions, handed off in prior leaf): 1 typography off-scale (alert-triage.css),
2 orphaned --fs-11/13/16 tokens, 3 spacing gaps off-scale (16), 4 ad-hoc :hover in app.css (17),
6 missing 75ch max-width, 12 unknown hexes (#d9a441 #7fb3ff #4caf50 #4caf7d).

## Note for Orchestrator / mirror owner
This is the SAME defect reverting a second time. Recommend pinning memory/designer/design_qa.py in
the mirror (PIN_FILES) or excluding it from auto-revert so the encoding fix stops getting clobbered.
The 6 genuine design regressions are real and owned by the design-token goal lane (see prior leaf).

## Verdict
Stale 'crashes: open' flag CLOSED with proof: gate is runnable on-host again and reports a single
authoritative number (6/12). Tooling defect re-fixed + verified.
