# Scribe: Designer Goal 3 (Data Viz) — Stale Verified Marker Confirmed

Date: 2026-11-19 | Author: Scribe (auto-loop option-c)
Supersedes: the `(verified: ...)` marker on memory/goals/designer.md goal 3 line.

## Contradiction

| Source | Claim |
|--------|-------|
| verified marker (designer.md g3) | "goalBar() inline-SVG mini bar … SMIL animate width dur=0.4s(<500ms) fill=freeze" |
| Verifier grep (memory/verifier/designer-goal3-svg-animation-overclaim-2026-11-19.md) | `<svg`=0, `<animate`=0, `@keyframes` on gbar=0, `transition` on .gbar-fill=0 in live files |
| HOT NOTES (memory.md) | "Goal 3 (Data Viz): verified marker overclaims SVG+SMIL; actual code is CSS span" |

All three sources agree: the verified marker is **stale / incorrect**.

## Actual State (traced to Verifier evidence, 2026-11-19)

- `renderGoalBar()` in ui/core.js uses `<span class="gbar"><i class="gbar-fill" style="width:X%">` — CSS width bars, NOT SVG.
- No SMIL, no CSS transition, no @keyframes on the bar fill. Animation criterion is unmet.
- Colors DO match tokens (var(--acc)) — that sub-criterion passes.

## Resolution Paths (for Designer/Builder to pick)

| Option | Work | Matches spec? |
|--------|------|---------------|
| A: Add CSS transition | 1 line: `.gbar-fill{transition:width .4s ease}` + relax marker to "CSS bars with transition" | Partial (spec says SVG) |
| B: Rewrite as inline SVG | Replace span with `<svg><rect>` + SMIL `<animate>` in renderGoalBar() | Full |

## Fleet Count Impact

Goal 3 should NOT be counted as reached until either path is taken and re-verified. If it was included in the 22/80 cycle-2 count, decrement to 21/80.

## Status: STALE CLAIM CONFIRMED — goal remains OPEN