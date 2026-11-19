# Goal 6 - Loading Skeleton Screens (progress 2026-11-19)

## What was done
1. **CSS added** to ui/app.css (appended at end): `.skel` class with shimmer animation (`@keyframes skel-shimmer`, opacity .3->.7, 1.5s infinite) + `prefers-reduced-motion` fallback (static opacity .4).
2. **Fleet panel** (`fleetUpdate()` in ui/core.js): Before the API fetch, if `#fleetBody` has no `.frow-h` children yet, injects 3 skeleton rows mimicking fleet host layout (dot + text bar). Skeleton is replaced when real data arrives.
3. **Goals panel** (`goalsLoad()` in ui/uploads.js): Before fetch, if `#goalsBody` has no `.gtile` children, injects 4 skeleton tiles matching the goal ring + name + meta layout (44px circle + two text bars). Replaced on load.
4. **Files/Uploads panel** (`filesLoad()` in ui/uploads.js): Replaced plain 'loading…' text with 5 skeleton list items (staggered-width bars + meta text bar), matching the real `#filesList li` structure.

## Design decisions
- Guard clause: skeleton only injected if target element is EMPTY (no existing content) - prevents flicker on polling refreshes (fleet polls every 5s).
- Uses design tokens (`var(--line)` for background, `border-radius:4px`) - consistent with token system goal #1.
- Shimmer animation respects `prefers-reduced-motion`.
- No new JS file needed; ~6 lines added per render function.

## Verification
- app.css braces: 279/279 balanced
- core.js braces: 218/218 balanced  
- uploads.js braces: 243/243 balanced
- Skeleton elements use same class names as real content (.frow-h, .gtile, li) so CSS layout applies identically -> zero layout shift on load.

## Remaining for full closure
- Browser rendering acceptance test (same shared blocker as goals #2/#5/#10: needs a live browser session to capture before/after screenshots proving no layout shift).
