# Verifier — Designer Goal 7 (Typography Hierarchy Audit) — 2026-11-19

**Verdict: FAIL (goal as specified cannot pass with current implementation)**

## Method
Static CSS audit of `ui/app.css` + `ui/tokens.css`. Extracted all 133 `font-size` declarations.
Checked each against the goal's 5-step scale: {12, 14, 15, 18, 24}px.

## Results
| Category | Count | Detail |
|----------|-------|--------|
| var() tokenized | 116 (87%) | Use --fs-* tokens; 8 of 12 tokens are off the strict 5-step |
| Literal ON-scale | 5 | Should be tokenized: .mh-card(12), .sub(12), .ft-detail(12), .ft-loading-label/.ft-error-sub(12), .chipfile .ficon(14) |
| Literal OFF-scale | **12** | Hardcoded px not on 5-step scale |

### 12 Off-Scale Violations (exact selectors)
| Value | Selectors |
|-------|-----------|
| 11px ×6 | .mh-k, .mh-d, code, .ft-dt-head em, .ft-chip, .fs-strip |
| 13px ×3 | .ft-hostname, .ft-dt-head, .ft-error-text |
| 10px ×3 | .fs-badge, .fs-lat, .fs-ts |

### Token Scale vs Goal Spec
tokens.css defines 12 font-size tokens. Only 4 match the goal's 5-step scale:
- ON: --fs-12(12), --fs-14(14), --fs-15(15), --fs-18(18)
- OFF: --fs-10, --fs-10-5, --fs-11, --fs-11-5, --fs-13, --fs-16, --fs-22, --fs-28
- MISSING: --fs-24 (h1=24px from goal spec has no token)

## Root Cause
The design system evolved a 12-step micro-scale (10→28) during Goals 1+3 implementation.
The Goal 7 spec (written pre-token-system) assumes a strict 5-step that was never the actual target.

## Recommendation to Designer
Two paths to closure:
1. **Relax spec** (recommended): Update acceptance to "all font-sizes use var(--fs-*) tokens; no hardcoded px" — current state is 87% there, just need to tokenize the 12 literals + 5 on-scale literals = 17 replacements.
2. **Strict 5-step**: Consolidate all 12 tokens down to 5 values (massive visual regression risk across fleet panel, goal bars, etc.)

Either way, Goal 7 stays OPEN until the 17 hardcoded px values are tokenized.

## Evidence Command
```
python -c "import re; css=open('ui/app.css').read(); print(len(re.findall(r'font-size\s*:\s*(?!var)', css)))"
# Expected: 17 (5 on-scale + 12 off-scale literals)
```
