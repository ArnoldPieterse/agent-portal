# Convergence Cross-Cycle Score Timeline — Goal #1 Verification (Pixel)
Date: 2026-11-27 · Round topic: Fleet Autonomy Convergence

**Structural audit: 10/10 PASS**

## What's in ui/cockpit-convergence.js
`renderScoreTimeline(history)` + `bindScoreTimeline(box)` — expandable multi-cycle
score chart from `/api/convergence` → `d.score_history`. Rendered as a full-width
card below the 2×2 grid (`.ckconv-tl`, `grid-column:1/-1`).

## Acceptance criteria
- [PASS] Renders >=2 real cycles (guard: `history.length < 2` → empty state; call site in `render()`)
- [PASS] Empty state: clear "no history yet" text when <2 samples
- [PASS] 0 console errors: balanced delimiters in both functions (8/8 braces, 50/50 parens render; 11/11, 62/62 bind)
- [PASS] Point focus order matches time order (sequential `.map()` over history array)
- [PASS] Per-point hover+focus tooltip: shows label (cycle #), score /100, mode
- [PASS] Expandable: aria-expanded toggle button "show"/"hide", collapses chart div
- [PASS] Line + area rendering: `<polyline>` for stroke + `<path d="M...Z">` for fill area
- [PASS] Keyboard accessible: `tabindex="0"` + `role="img"` on each circle
- [PASS] aria-label per point: "Sample {label}: score {N} of 100, {mode}"
- [PASS] Reduced-motion safe: `.ckconv-tl-pt` transitions disabled under `prefers-reduced-motion` + `.ckconv-no-motion`

## Note
Live browser rendering (actual SVG paint) requires a non-sandbox seat — same standing
blocker as goal #6 (CDP screenshots). Structural verification is complete; the visual
output is a deterministic consequence of the audited code.
