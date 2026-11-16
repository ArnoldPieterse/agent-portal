# Goal #4 Evidence — Micro-interactions & Motion Budget
Date: 2026-11-16
File: index.html (live)

## Verification Results

| Check | Result |
|-------|--------|
| Transitions <=200ms | PASS (6 transitions, max 200ms) |
| prefers-reduced-motion guard | PASS |
| Hover states present | PASS (6: acard, btn, chipfile, flink, gtile, msg) |
| Active/press state present | PASS (btn: scale(0.97)) |

## What was added this pass

CSS block inserted before `</style>` in index.html:
- `.msg:hover` — background + border-color transition 150ms
- `.btn:hover` / `.btn:active` — border-color 150ms + transform scale(0.97) 80ms
- `.acard:hover` — border-color + background 150ms
- `.chipfile:hover` — border-color + opacity 150ms
- `.gtile:hover` — background + border-color 150ms
- `@media(prefers-reduced-motion:reduce)` — kills all transitions/animations

All durations use `var(--dur-fast,150ms)` token reference (goal #1 integration).

## Open items for full PASS
- Screenshot pair on :8099 (blocked: portal restart pending)
- Manual interaction before/after (needs live page)
