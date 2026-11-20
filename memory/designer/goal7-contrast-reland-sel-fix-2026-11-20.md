# Goal 7 - Color Contrast + Accessibility: re-land token fixes + selection-state fix (2026-11-20)

## Context
Previous pass documented token-level AA fixes in `goal7-contrast-token-fixes-2026-11-20.md` but the changes
were reverted (mirror cycle). This pass re-applies all fixes AND implements the documented follow-up:
component-level selection-state text color.

## Changes applied to ui/tokens.css
**Light theme ([data-theme=light]):**
| Token | Before | After | Reason |
|-------|--------|-------|--------|
| --ok | #1f9d5b | #177443 | 2.71-3.48:1 -> PASS on light surfaces |
| --warn | #c47a12 | #8d580d | 2.66-3.42:1 -> PASS |
| --err | #d64545 | #b43a3a | 3.41-4.38:1 -> PASS |
| --faint | #7a8699 | #646e7d | 2.87-3.69:1 -> PASS (used 16x) |
| --acc | #2f6fe0 | #2d69d5 | 3.65-4.49:1 -> PASS on near-white |
| --sel-dim | (new) | #5a6678 | Component-level AA on sel-bg (4.53:1) |
| --muted | (new) | #5f6472 | Was falling back to dark value |
| --warn-text | (new) | #7b6123 | Was 1.5-1.9:1 fallback on light |

**Dark theme (:root):**
| Token | Before | After | Reason |
|-------|--------|-------|--------|
| --muted | #8b93a7 | #9097ab | Clears sel-bg 4.29->4.52:1; no regression elsewhere |

## Changes applied to ui/app.css
Added rule after `.acard.sel`:
```css
.acard.sel .nm span,.acard.sel button{color:var(--sel-dim,var(--dim))}
```
Uses `var(--sel-dim, var(--dim))` fallback so dark theme (where --sel-dim is undefined) uses --dim which already passes at 5.40:1 on dark sel-bg.

## Verification
- `python memory/designer/contrast_audit.py` => DARK ALL PASS, LIGHT ALL PASS, exit 0
- Selection-state: light --sel-dim on #d4e4ff = 4.53:1 PASS; dark --dim on #20304d = 5.40:1 PASS
- No regression: all tokens that previously passed still pass (script checks all primary text tokens on all main surfaces)

## Remaining (documented, not a token failure)
--faint/--acc/--link dip below 4.5 ONLY when rendered on --sel-bg but are NOT used inside .acard elements.
If future components place these on selection backgrounds, they'll need the same component-level override pattern.
