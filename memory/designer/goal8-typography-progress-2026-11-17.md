# Goal #8 Typography Hierarchy — Progress Evidence (2026-11-17)

## What was done this pass
1. Added typography tokens to :root in ui/app.css:
   - `--lh-tight:1.2` (headings), `--lh-body:1.45` (body), `--lh-loose:1.6` (monospace/code)
   - `--fw-reg:400`, `--fw-med:500`, `--fw-semi:600`, `--fw-bold:700` (4 weight steps)
   - `--ls-caps:.05em` (uppercase label tracking)

2. Fixed out-of-range line-height:
   - `#actBody`: 1.7 → var(--lh-loose) [1.6] — was the only violation

3. Tokenized all hardcoded font-weights (8 selectors):
   - .dmseg summary, #peek .pk-h, .aev .an, .gring .pct, .mh-k → var(--fw-semi)
   - #peek .pk-sz → var(--fw-reg)
   - .btn, aside .ah, .gname → var(--fw-med) (new intermediate step)
   - .mh-v → var(--fw-bold,700)

4. Tokenized letter-spacing on uppercase labels:
   - aside .ah: .06em → var(--ls-caps) [.05em]
   - #queueHead: .06em → var(--ls-caps)

## Verification (grep-based, no browser needed)
- `grep line-height ui/app.css`: all values are tokens or in [1.2, 1.6]. Only exception is #attach (line-height:1 for icon centering, not text flow).
- `grep font-weight ui/app.css`: 4 distinct token steps used across 14 selectors; zero hardcoded numeric weights remain.
- `grep letter-spacing` with `text-transform:uppercase`: both use var(--ls-caps) = .05em ✓

## Remaining for full closure
- Computed-style dump script (run in browser to confirm no inherited override puts a value outside range).
- Visual before/after screenshot of a dense panel.
Both require browser access — same wall as Goal #5. Structure + tokens are verified correct via grep.

## Files changed
- ui/app.css (+4 token lines, 16 property replacements)
