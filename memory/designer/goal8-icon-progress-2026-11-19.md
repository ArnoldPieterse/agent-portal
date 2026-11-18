# Goal #8 Icon System — progress leaf (2026-11-19, Designer)

parent: memory/goals/designer.md | sibling: ui/core.js, ui/app.css

## What changed this pass
Replaced the 4 genuine UI icon SLOTS in `ui/core.js` with the SVG icon set:
| slot | before | after |
|---|---|---|
| agent-card avatar fallback | `🤖` | `UI.icSVG("agent",18)` |
| edit-profile button | `⚙` (textContent) | `UI.icSVG("settings",14)` (innerHTML) |
| delete button | `✕` (textContent) | `UI.icSVG("close",14)` (innerHTML) |
| tool chip prefix | `🔧 ` (textContent) | `UI.icSVG("tool",13)+<span>esc(tn)</span>` |

## Verification
- Emoji recount on core.js: 🤖/⚙/✕/🔧 → count 0 each; total glyphs 34→25.
- Edits are in-line string swaps inside existing statements (no structural change). No Node on this host, so no `node --check`; low-risk by inspection.

## Live icon set (correction to goal text)
The ACCEPTED set is `core.js` `ICONS` = **22 icons**, exposed as `UI.icon()`/`UI.icSVG()`, and it IS loaded by index.html. `ui/icons.js` (21 icons) is a parallel copy NOT in the script list — dead code; do not depend on it.

## Remaining for closure (next pass)
1. Prose status prefixes `⚠`x17 / `✓`x6 inside `.textContent` & `notify()` — need textContent→innerHTML conversion (larger, layout-sensitive).
2. `ui/uploads.js`: `⚠`x4, `🤖`, `↻`.
3. `index.html` shell emoji (🤖/🎯/🛰/📁/🔧) — pinned + markup-only → requires repin before editing.
