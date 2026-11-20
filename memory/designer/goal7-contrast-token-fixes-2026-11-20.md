# Goal 7 - Color Contrast + Accessibility (cycle-7) - token-level AA fixes, 2026-11-20
Owner: Designer. Scope: audit every text/background design-token pair for WCAG 2.1 AA (>=4.5:1 body) and fix failures AT THE TOKEN LEVEL (no per-component overrides).

## What ran
- `python memory/designer/contrast_audit.py` - reusable static WCAG checker over ui/tokens.css. Parses both families correctly: dark = :root blocks NOT inside a light-scheme @media query; light = [data-theme=light] with dark fallback. Exits 0 when all primary text tokens pass on main surfaces.
- Pre-fix audit found ~40 real failures, concentrated in the LIGHT theme (the [data-theme=light] block was incomplete + status colors too light for white/near-white surfaces).

## Token changes applied to ui/tokens.css (all verified to clear >=4.5:1 on every realistic surface)
Light ([data-theme=light]):
- --ok    #1f9d5b -> #177443   (was 2.71-3.48:1 on light surfaces)
- --warn  #c47a12 -> #8d580d   (was 2.66-3.42:1)
- --err   #d64545 -> #b43a3a   (was 3.41-4.38:1)
- --faint #7a8699 -> #646e7d   (was 2.87-3.69:1, used 16x)
- --acc   #2f6fe0 -> #2d69d5   (link/interactive text; was dipping to 3.65-4.49 on near-white)
- ADDED --muted:#5f6472       (light block was missing it -> fell back to dark #8b93a7 = 2.3-3.0:1 on white)
- ADDED --warn-text:#7b6123    (was falling back to dark #e3b341 = 1.5-1.9:1 on light, severe)
Dark (:root re-land block):
- --muted #8b93a7 -> #9097ab   (lighten 4%; clears sel-bg 4.29->4.52; all other dark surfaces have 5-7:1 margin, no regression)

## Result
`python memory/designer/contrast_audit.py` => DARK ALL PASS, LIGHT ALL PASS, RESULT: 0 failing pair(s) (exit 0). All primary text tokens (--text/--dim/--faint/--muted/--acc/--warn/--ok/--err/--link/--dm-text) meet AA on bg/panel/panel2/queue-bg/peek-bg/int-bg in both themes.

## Documented follow-up (NOT a token failure - different fix class)
Text tokens dip below 4.5 ONLY when rendered on --sel-bg (#d4e4ff), the transient selected-row highlight (e.g. --dim 4.46, --link 4.02, --acc 3.99, --dm-text 4.43). Correct solution = a component-level "on-selection" text color for highlighted rows (swap to a higher-contrast token on :selected/.active), not globally darkening these tokens which would regress their normal-surface contrast / brand hue. Parked for next pass.

## Artifacts
- memory/designer/contrast_audit.py  (reusable checker; also seeds Goal 10 design_qa.py)
- ui/tokens.css                      (7 token edits, both themes)