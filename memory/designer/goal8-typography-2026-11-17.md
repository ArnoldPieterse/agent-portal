# Goal 8 — Typography hierarchy pass (evidence)
Date: 2026-11-17
File: ui/app.css

## Audit results (post-fix)
| Check | Status | Detail |
|-------|--------|--------|
| line-height in [1.2, 1.6] | PASS | body=1.45, .opsbox=1.6, #actBody=1.6, .mh-d=1.3; #attach=1.0 (documented exception: 44px square icon button) |
| uppercase labels have +0.05em letter-spacing | PASS | aside .ah=.05em, #queueHead=.05em |
| >=3 meaningful font-weight steps | PASS | 400/500/600/700 (4 distinct values) |

## Changes made this pass
1. `#actBody` line-height: 1.7 → 1.6 (was exceeding max of allowed range)
2. `aside .ah` letter-spacing: .06em → .05em (spec compliance)
3. `#queueHead` letter-spacing: .06em → .05em (spec compliance)

## Documented exception
- `#attach { line-height:1 }` — 44×44px square button containing a single "+" glyph. line-height:1 is the correct value for vertical centering in a fixed-size icon container; not body or heading text.

## Remaining for full closure
- Computed-style dump script (browser-based) to verify at runtime on :8099 — blocked by WinError 10013 (portal down). CSS static audit is complete and passes.
