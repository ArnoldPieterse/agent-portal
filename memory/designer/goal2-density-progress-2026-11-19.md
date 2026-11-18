# Goal #2 - Information Density Pass: Progress 2026-11-19
## Action taken
Replaced all 7 hardcoded line-heights in ui/app.css with design token references:
| Location | Before | After (token) |
|---|---|---|
| body | 1.45 | var(--lh-base)=1.3 |
| .opsbox | 1.6 | var(--lh-mono)=1.35 |
| #actBody | 1.7 | var(--lh-mono)=1.35 |
| .mh-d | 1.3 (hardcoded) | var(--lh-base)=1.3 |
| .sub | 1.5 | var(--lh-base)=1.3 |
| .ft-tooltip | 1.5 | var(--lh-base)=1.3 |
| .ft-models | 1.6 | var(--lh-mono)=1.35 |

Also tokenized: .qrow padding (3px→var(--sp-3)), .mh-card padding+radius.

## Impact
- Body text vertical density: ~10% tighter (1.45→1.3)
- Mono panels (ops, activity): ~16-20% tighter (1.6-1.7→1.35)
- No font-size changes; no clipping risk

## Remaining for full closure
- Before/after screenshots (requires browser render)
- Check if any panel-specific padding can be further reduced
