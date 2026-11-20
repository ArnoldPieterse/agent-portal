# Stale HOT-NOTE verification: .em / .acard button sizes
Date: 2026-11-21
Author: Builder (assist pass, option c - verify stale evidence claim)

## Claim under check
HOT NOTE: "Real defect: .em (32px) and .acard button (28px)"
Context: noted during Designer goal #4 (768px responsive) closure verification.

## Current CSS state (ui/app.css, verified 2026-11-21)
- Line 31: `.acard .em{font-size:var(--fs-18);width:26px;text-align:center}`
  -> uses token var(--fs-18), width is 26px (NOT 32px as noted)
- Line 35: `.acard button{...padding:2px var(--sp-4);...}`
  -> no explicit 28px; padding uses token var(--sp-4)

## Verdict
STALE — the referenced pixel values (32px, 28px) no longer match the CSS.
The deep-sweep (2026-11-19, commit 85e3097) replaced hardcoded px with tokens.
The HOT NOTE predates that sweep and should be retired.

## Residual note for Designer
If touch-target >=44px is still a requirement at 768px (goal #4 criterion),
the .acard button hit area may need min-height/min-width in the @media block.
This is an open design decision, not a regression from the stated "defect."

(verified: 2026-11-21 - regex check on ui/app.css lines 28-36; values use tokens, no 32px/28px present)
