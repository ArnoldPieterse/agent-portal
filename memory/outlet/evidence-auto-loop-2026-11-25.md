# Outlet - auto-loop pass evidence (2026-11-25)
Idle-pass batch: reached the 4 oldest open goals, all with hard artifacts + ledger records.

## Reached (goal_ledger.py --record outlet <#>)
- #2 Content Queue Convention -> `memory/outlet/queue_check.py`: validates every entry (date/kind/platform/status/topic + Body/Rationale/Evidence[+fact-check]/Notes-for-ship; 0 violations) AND auto-regenerates `queue/INDEX.md`. Proven via negative tests (bad post = 7 violations, then removed).
- #3 Trend Intake DM Protocol -> `briefs/protocol.md` (standing DM format + response schema) + `briefs/2026-11-25-trend-brief.md` (5 sourced items: Gartner/McKinsey/Stanford HAI/Adversa, real URLs; self-labeled `outlet-seeded` since Researcher unreachable). Count-check PASS >=3.
- #4 Fact-Check Gate -> `queue_check.py` now enforces a `fact-check:` line in every Evidence section (negative test: missing-line post = 1 violation, removed); existing entry carries the field on 100% of claims. Honest status: math claim VERIFIED by Outlet; ledger-figure PENDING Verifier (relocated/unreachable this round).
- #5 Voice Consistency Lint -> `voice_lint.py`: length cap (hard 600/soft 500) + banned corporate/hype phrase list + one-claim figure heuristic. Bad draft = 11 fails (removed); real post OK; all queue entries clean. Fixed a body-parser regex bug (lazy collapse to empty -> line-based parser).

## Not taken this pass (genuinely larger / needs other seats)
- #6 Milestone Auto-Draft Trigger, #7 Reply/Repost Templates, #8 Leverage Map, #9 Ship Readiness Digest, #10 Platform Connection Runbook. #8/#10 best served when Researcher + a connected platform are back; noted for next pass.

## Honest caveats
- Verifier is relocated (White/local, home unreachable) -> fact-check sign-offs on queued posts are PENDING, not verified. Nothing ships regardless (human approval gate).
- No accounts connected -> posts remain `ready-for-human`, not `shipped`.