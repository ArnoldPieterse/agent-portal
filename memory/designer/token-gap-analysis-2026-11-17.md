# Designer Goal #1 - Token Layer Gap Analysis (Scribe audit 2026-11-17)

Parent: memory/goals/designer.md goal #1
Status: 23 tokens defined; 3 categories missing (radius, shadow, motion-duration)

## Current tokens (:root, ui/app.css line 6)
Colors: --bg --panel --panel2 --line --text --dim --faint --acc --ok --warn --err --focus
Spacing: --sp-4 --sp-8 --sp-12 --sp-16 --sp-24
Font-size: --fs-11 --fs-12 --fs-13 --fs-14 --fs-15 --fs-16

## Missing token categories + exact values to add

### radius (3 unique hard-coded values, 30 occurrences)
--radius-sm: 6px   (badges, chips, small elements)
--radius-md: 8px   (buttons, inputs, cards - most common)
--radius-lg: 12px  (panels, modals)

### shadow (check for box-shadow; none found in current scan - add when needed)
--shadow-sm: 0 1px 3px rgba(0,0,0,.3)   (cards)
--shadow-md: 0 4px 12px rgba(0,0,0,.4)  (panels, popovers)

### motion-duration (0 found in current CSS - future-proofing for goal #4)
--dur-fast: 150ms  (hover, focus)
--dur-med: 200ms   (panel expand/collapse - goal #4 budget cap)
--dur-slow: 300ms  (page transitions if added)

## Hard-coded colors that SHOULD become tokens (generic, reused)
| Value    | Occurrences | Suggested token  | Notes |
|----------|-------------|-----------------|-------|
| #fff     | 3x          | --on-accent     | button/segment text on accent bg |
| #8b949e  | 3x          | --dim-alt       | queue panel dim text (slightly different from --dim #9aa7b8) |
| #2a3342  | 2x          | --line          | ALREADY a token! Replace hard-coded with var(--line) |
| #9ccaff  | 2x          | --link-hover    | link hover color (lighter than --acc) |

## Hard-coded colors that are INTENTIONALLY component-specific (do NOT tokenize)
- Agent status dot colors: #3ddc84, #ffb454, #e05252, #888 (fdot class)
- DM segment: #4a3f6b, #b79ce0 (purple theme for private messages)
- You-message bubble: #243b63, #33507f (distinct from panel colors by design)
- Peek overlay: #141a26, #2c3548, #cdd3e0, #aab2c5 (isolated component palette)
- Interrupt banner: #d29922, #2d2000, #e3b341 (warning-specific)
- Queue spinner: #30363d, #58a6ff (GitHub-dark specific to that panel)

## Action items for Designer
1. Add --radius-sm/md/lg + --on-accent + --link-hover to :root (5 new tokens)
2. Replace 30 border-radius:Npx with var(--radius-*)
3. Replace #fff on accent buttons with var(--on-accent)
4. Replace the 2x #2a3342 hard-codes with var(--line) (already exists!)
5. Optionally add --dim-alt for queue panel or just use --dim (close enough: #9aa7b8 vs #8b949e)
6. Shadow + motion tokens: add as placeholders, wire in when goals #4/#10 need them

## Verification (goal acceptance test)
grep confirms every hard-coded color/radius/duration replaced by var(--token); file index-linked.
After step 1-5 above, remaining hard-coded hexes should be ONLY the component-specific ones listed above.
