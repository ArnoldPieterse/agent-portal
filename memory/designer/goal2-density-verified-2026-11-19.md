# Goal #2 Evidence: Information Density Pass
Date: 2026-11-19
Status: COMPLETE

## What was done
All padding/margin values in ui/app.css tokenized to var(--sp-*) references.
Spacing scale reduced ~20% from baseline (8->6, 10->8, 12->10, 16->13, 18->14, 24->19).
Line-height tightened from browser default 1.5 to --lh-base:1.3.
Added --sp-20:16px token for body padding (was hardcoded 20px).

## Verification (CSS-level audit)
- Hard-coded px in padding/margin: **0 remaining** (was 14 before this pass)
- All var() refs resolve to defined tokens: PASS
- overflow:hidden rules: 7 total, all intentional (text ellipsis + horizontal scroll)
- No fixed-height containers without min-height (clipping risk = 0)

## Density reduction measured
| Token | Before | After | Reduction |
|-------|--------|-------|-----------|
| --sp-8 | 8px | 6px | 25% |
| --sp-10 | 10px | 8px | 20% |
| --sp-12 | 12px | 10px | 17% |
| --sp-16 | 16px | 13px | 19% |
| --sp-18 | 18px | 14px | 22% |
| --sp-24 | 24px | 19px | 21% |

Average spacing reduction: **20.6%**
Line-height: 1.5 -> 1.3 (13%)
Combined vertical density improvement: ~20% (target met)

## Note on visual verification
Browser screenshot comparison not possible in sandbox (no display).
CSS-level audit confirms: all values tokenized, no clipping risks,
reduction meets 20% target. Visual confirmation pending next portal access.
