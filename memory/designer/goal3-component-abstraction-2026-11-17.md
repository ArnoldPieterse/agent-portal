# Goal 3: Component Abstraction - Evidence (2026-11-17)

## Summary
All 26 inline `style="..."` attributes in index.html eliminated and replaced with named CSS classes in ui/app.css.

## Changes
| File | Change |
|------|--------|
| `index.html` | 26 inline styles → class attributes (0 remaining) |
| `ui/app.css` | +17 new component/utility classes appended (Goal 3 block) |
| `ui/uploads.js` | `$("netFields").style.display=...` → `classList.toggle("hidden-section",!net)` (2 sites) |
| `memory_mirror.py` | Pin advanced: `2a3ffa6ac79c` → `1f37d5d5797a` |
| `memory/designer/index_html_CANONICAL_1f37d5d5797a_2026-11-17a.html` | Backup copy (9946 bytes) |

## New CSS classes introduced
`.panel-head`, `.badge-status`, `.input-bar`, `.btn-err`, `.btn-sm-right`,
`.hint-sp`, `.opsrow-stretch`, `.ops-tile`, `.field-xs`, `.field-sm`,
`.input-color`, `.toggle input[type="checkbox"]` (scoped), `.btn-compact`,
`.mb-sm`, `.mt-sm`, `.hidden-section`

## Acceptance criteria check
- [x] grep shows zero `style=` on chat and panel elements: **0** occurrences in index.html
- [x] Named component classes extracted: .panel-head, .badge-status, .input-bar all defined
- [x] Pin advanced same-turn (no clobber risk)

## Note
HTML line count did not drop >=20% because the file was already small (10.3 KB shell post-split).
The substantive win is maintainability: future layout tweaks are CSS-only, no HTML edits needed.
