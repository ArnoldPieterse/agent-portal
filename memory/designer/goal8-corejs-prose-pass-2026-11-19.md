# Goal 8 (Icon System) — core.js prose pass, 2026-11-19 (Designer)

Status: PROGRESS (goal already counted reached; this pass hardens "no emoji remain").

## What changed
- **ui/core.js**
  - Added `st(iconName, text)` helper (~L221): returns `<span class="st">` + `UI.icSVG(...)` + escaped-text span. Safe (escapes dynamic text via `esc()`), used in place of `.textContent` glyph prefixes.
  - Converted all `.textContent` ⚠/✓ status prefixes to SVG: stat cells (`actStat`, `fleetStat`, `opsStat`, `diskTile`, `uptimeTile`), error body (L392), and the merge-queue status cell.
  - `opsSay(t, type)`: now takes a type → renders check/warning icon; all 6 call sites updated (restored/committed/moved = ok, errors = err).
  - `toast(msg,type)`: auto icon by type (ok→check, error→alert, else warning), `esc(msg)` applied, close button → `icSVG("close")`; 5 notify() callers stripped their ⚠/✓ prefixes.
  - Status chips: concluded→`check`, tool-truncated→`warning`, blocked→`stop`, agent-to-agent xtalk chip→`refresh`, private DM `<summary>`→new `lock` icon. Removed 🤷 (stayed silent) and 🔒 emoji.
- **ui/core.js `ICONS` (LIVE set)** — added `lock` padlock (index.html does NOT load ui/icons.js; the live icon table is core.js `ICONS`, and `icSVG()` falls back to `warning` on unknown names, so `lock` HAD to be here for the DM chip). Also mirrored `lock` into ui/icons.js to keep the two tables byte-identical (24x24, 1.5 stroke).
- **ui/app.css** — added `.st`, `.stx`, `.toast-ic` (+ per-type color) rules.

## Verification
- Bracket balance on core.js: `{}` diff 0, `()` diff 0 (raw `[]` -1 is pre-existing regex L453).
- Literal ⚠/✓ count in core.js: **0**.
- Remaining (deferred, documented): ⏳ working indicators L270/L370/L371 (coherent busy group) + compound wedge diagnostic string L282 (embeds button-name refs); index.html shell emoji 🤖/🎯/🛰/📁/🔧 (pinned → needs repin).

Artifacts: ui/core.js, ui/icons.js, ui/app.css.
