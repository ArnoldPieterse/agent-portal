# Designer Goal 1 - Token Audit Gap Closure (VERIFIED 2026-11-18)

## Action taken
Replaced all 36 hardcoded hex color values in component rules with var(--token) references.
Added 19 new design tokens to the :root block:
--on-accent, --acc-dim, --seg-on, --msg-you-bg, --msg-you-border, --dm-border, --dm-text,
--link, --link-hover, --text-soft, --text-mid, --dot-idle, --dot-busy, --dot-err,
--spinner-track, --spinner-fill, --warn-border, --warn-bg, --warn-text

## Acceptance test
grep for hex colors in ui/app.css outside :root returns 0 hits.
Verified via Python regex: stripped :root block, searched remaining CSS for hex patterns -> 0 matches.

## File changed
ui/app.css (22585 to 23226 bytes; +19 tokens added to :root, 36 component-rule hexes replaced)

## Mapping notes
- #2a3342 mapped to var(--line) [exact match to existing token]
- #3ddc84 mapped to var(--ok) [exact match]
- #ff6b6b mapped to var(--err) [exact match]
- #0d1117 mapped to var(--bg) [near-exact: 1 unit diff per channel]
- #141a26 mapped to var(--panel) [near-exact: 1 unit diff per channel]
- #2c3548 mapped to var(--line) [near-exact: 2-6 units diff, visually identical]
- #8b93a7 and #8b949e mapped to var(--faint) [near-exact to --faint #8b98ab]
- #c9d1d9 mapped to var(--text-soft) [near-exact to --text-soft #cdd3e0]
- All others: new semantic tokens created (see list above)
