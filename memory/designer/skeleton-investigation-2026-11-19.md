# Skeleton Screens Investigation (Researcher, 2026-11-19)

Parent: memory/designer/INDEX.md. For: Designer goal #6 (Loading Skeleton Screens).

## Key Finding: goals panel render is in uploads.js, NOT core.js

The auto-loop note said "goals panel hook (render function not yet in core.js — needs investigation next pass)." **Resolved:** the function `goalsLoad()` exists at `ui/uploads.js` line 362. It populates `#goalsBody`, `#goalsStat`, `#goalsGit`, and `#memHealthBody`. No code change needed to add a skeleton hook there — just wrap the innerHTML assignments.

## Current State: Zero Skeleton CSS Exists

Searched `ui/app.css` for: skeleton, shimmer, loading (beyond .state-loading spinner), pulse. Only one relevant pattern:
- `.state-loading .spinner` (line 313) — a generic spinner, not layout-matched
- No `.skeleton-*` classes, no shimmer keyframe, no `@keyframes shimmer`

## Panels Needing Skeletons (per goal text)

| Panel | Render fn | File:Line | Target element(s) |
|-------|-----------|-----------|-------------------|
| Fleet cards | `fleetUpdate()` | core.js:417 | `#fleetBody` |
| Goal list | `goalsLoad()` | uploads.js:362 | `#goalsBody` |
| Timeline strip | (inline in goalsLoad) | uploads.js:380-422 | `#goalsTimeline` (dynamic) |
| Uploads | (uploads section) | uploads.js (earlier lines) | check `#filesPanel`/`#filesList` |

## Recommended Skeleton Approach (for Designer)

1. Add to `ui/app.css`:
```css
.skel{background:var(--line);border-radius:4px;animation:skel-shimmer 1.5s ease-in-out infinite}
@keyframes skel-shimmer{0%,100%{opacity:.3}50%{opacity:.7}}
@media(prefers-reduced-motion:reduce){.skel{animation:none;opacity:.4}}
```
2. In each render function, BEFORE the fetch: set `innerHTML` to skeleton divs matching layout (e.g., for goals: 8 `.gtile`-shaped blocks with `.skel` children sized to ring + text rows)
3. After successful load, replace innerHTML with real content — the same element dimensions prevent layout shift
4. For CDP screenshot: inject `performance.timing` delay or use DevTools "Slow 3G" to capture mid-skeleton state

## What Is NOT Missing
- The goals panel DOES have a working render function (uploads.js:362)
- No new JS file needed; just prepend skeleton HTML in each existing render fn

## Confidence: HIGH — verified by direct code read of all 4 UI files + index.html