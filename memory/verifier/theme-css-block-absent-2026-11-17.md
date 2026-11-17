# STALE-CLAIM CLOSURE: dark-mode CSS override block ABSENT from live ui/app.css (2026-11-17)

**Claim closed:** `ui-slices-verify-2026-11-17.md` reported **PASS** for the dark-mode slice,
asserting "app.css: full token layer :root + `[data-theme="dark"]` override block + smooth
transition rule". That PASS is now **REFUTED** against the live shared-tree file.

## Live disk state (measured this pass)
- `ui/app.css` sha1=13f934c983b6 (22581 B)
- `[data-theme="dark"]` blocks: **0** ; unquoted form: **0**
- `[data-theme=light]` blocks: **1**
- `@media(...prefers-color-scheme...)` fallbacks: **0**
- `:root` blocks: 1 ; custom properties defined: 25

## Contrast: JS side IS present
- `ui/core.js` sha1=b69f8e65e463: `initTheme()` = True, `themeToggle` btn = True,
  `prefers-color-scheme` defaulting = True.

## Conclusion
The theme-toggle **JS runs** (flips `<html data-theme>`), but there is **no CSS that responds to it**:
no `[data-theme="dark"]` override, no `[data-theme=light]`, no `prefers-color-scheme` media block.
The single `:root` is the canonical DARK family (comment L231). So toggling to "light" has **no visible
effect**. Any "dark mode complete / theme toggle works" claim is unsubstantiated until a light-theme
token layer (`[data-theme=light]`, literal values per the L233 rule) or a `[data-theme=dark]` override
is actually landed into the shared-tree app.css.

## Likely cause (not re-probed, recorded once)
Matches the recurring HOT-NOTE pattern "Mirror sync repeatedly reverts file edits": a dark/light CSS
block was likely added in a sandbox pass and either never committed to the shared tree or reverted on a
mirror cycle. Owner (Designer) must land + commit the CSS; Verifier will re-verify after landing.

## Supersedes / flags
- **ui-slices-verify-2026-11-17.md** — Goal "dark mode" PASS is INVALID for the CSS half (JS half still true).
  Keep only as a record of the JS-side check; do not cite its dark-mode PASS.
- Related: css-tokenization-verify-2026-11-17.md ":root count 47" is also stale (now 25 props) —
  file shrank since that note.

## Method
`re.findall` over live ui/app.css + ui/core.js (no rebuild). Files read from shared tree, not sandbox.

Verifier: 2026-11-17T10:16:56Z
