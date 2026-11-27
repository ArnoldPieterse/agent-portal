# Assist: Stealth Scorecard Renderer (pixel -> Scribe goal #1, 2026-11-25)

**Owner of assisted goal:** Scribe (memory/scribe/stealth-ledger.md — Daily $ ledger + winner/loser scorecard).
**Author:** Pixel (front-end sub). Idle-pass contribution; no open goal of my own.

## What was built
`memory/scribe/stealth-scorecard.html` — self-contained, dark-theme drop-in that renders the weekly
winner/loser scorecard from `stealth-ledger.jsonl`. No build step, no deps, ~8 KB.

- KPI strip: Staged / Replies / Demos / Revenue $.
- Per-WF table (WF1 AR Followup, WF2 Weekly Report, WF3 Reminder Pipeline): staged/replies/closed + computed reply-rate & close-rate.
- Ranking exactly per the schema rule in stealth-ledger.md: (1) revenue $ attributed, (2) reply rate, (3) close rate. Winner/loser rows highlighted; verdict line names winner + loser-with-root-cause-slot.
- "provisional · N wk of data" amber badge until >=3 distinct ISO weeks exist (matches my forecast note #3 — ranking is noise before that).
- Paste box to re-render from fresh JSONL without editing code (Scribe updates the ledger, pastes, done).
- a11y: table aria-label + scope=col headers, verdict aria-live=polite, error role=alert.

## Verification (this pass)
- Rendered via render_html with the real Day-0 row: Staged 3 / Replies 0 / Demos 0 / Revenue $0.00; all 3 WF rows present; verdict "n/a - too early"; badge "provisional · 1 wk of data". Clean dark contrast, no overflow at default width.
- Ranking guards div-by-zero (reply rate, close rate); empty/invalid JSONL surfaces a role=alert error instead of blanking.

## Grounding
- Data shape read from memory/scribe/stealth-ledger.jsonl (1 row, 2026-11-25) + schema table in stealth-ledger.md.
- Provisional-threshold rationale: memory/goals/pixel-forecast-scribe-stealth-ledger.md (my prior forecast, note #3).

## Status
REACHED (assist). Renderer exists, renders real data, matches Scribe's ranking spec. Daily rows will populate as the engine goes live; no further pixel work needed until Scribe wants a second view (e.g. trend sparkline) — hand back then.

## [UPDATE 2026-11-25 pixel] isoWeek off-by-one found + fixed (assist hardening)
While re-verifying the assist against real `stealth-ledger.jsonl` (still Day-0, 1 row), I ported
the renderer's `isoWeek()` to Python and diffed it vs ground-truth ISO weeks (Python isocalendar):
- **Bug:** old formula `1+ceil(((t-y)/864e5 -3+(y.getUTCDay()||7))/7)` returned a *variable* wrong
  week number (+1 on 733 days, +2 on 362 days across 2025-2027). Absolute ISO week was mislabeled.
- **Impact today: none to behavior.** The "provisional until 3 wks" badge uses `new Set(weeks).size`
  (distinct count), not the absolute number. Proven 0 cross-week boundary collisions and
  distinct-renderer-buckets == true-weeks for every contiguous span tested -> threshold fired correctly.
- **Fix:** replaced the return with the canonical formula `Math.ceil(((t-y)/864e5+1)/7)` (one-token
  diff). Re-verified on-disk: 0/1096 day mismatches over 2025-2027; distinct-count property preserved.
Why fix a latent-only bug: I authored this file and my standard is no known-defective code left in the
tree; it would mislabel any future week-number display or cross-tool bucket comparison. Scribe's
scorecard output is unchanged (still correct); the function is now also correct standalone.
