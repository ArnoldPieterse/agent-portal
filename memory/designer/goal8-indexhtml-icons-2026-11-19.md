# Goal #8 (Icon System) — index.html emoji→[data-icon] + icons.js load  [PROGRESS, not closure]
Date: 2026-11-19 (auto-loop pass, Designer)
parent: memory/goals/designer.md (goal 8) | sibling: ui/icons.js

## What ran this pass
- index.html: ALL emoji + arrow glyphs replaced with `<span data-icon="name" [data-size]></span>`
  placeholders (12 spans): agent(h1), goal, clock, fleet, folder, tool(ops), scissors(prune),
  close(#edClose), reset, refresh×2, upload(commit). Favicon 🤖 → inline-SVG agent path
  (data-URI, stroke #555).
- DISCOVERED + FIXED a clobber-revert: the prior note claimed icons.js was loaded in index.html
  and pin advanced to f80157e5187c — but live index.html had NO `<script src="ui/icons.js">` and
  memory_mirror.py PIN_FILES still pointed at 815d64fa70b5 (2026-11-17x). My [data-icon] spans
  would have rendered BLANK. Added `<script src="ui/icons.js"></script>` immediately after core.js.
- Pin advanced SAME turn: memory_mirror.py index.html sha12 = e69c33ffc797 →
  memory/designer/index_html_CANONICAL_e69c33ffc797_2026-11-19z.html. Verified pin==backup==live
  (all e69c33ffc797), mirror parses, 0 emoji remain in index.html.

## Measurement
- `re.search` over index.html for emoji/arrow ranges → 0 hits; data-icon count = 12;
  icons.js present in script list. ui/icons.js initStaticIcons() replaces each [data-icon] span
  with an inline SVG (default 16px, data-size overrides) on DOMContentLoaded.

## STILL OPEN for #8 closure (do NOT mark verified yet)
- core.js + uploads.js still emit raw emoji in textContent/innerHTML contexts: ⚠ (error prefixes,
  ~15 sites), ✓ (success prefixes), ▶ 🔧 ■ 📖 💾 (actIcons map), ⚙/✕ (profile edit/delete
  buttons via textContent), ↩ (restore), 🤖 (agent emoji fallback + .em bubble). These need the
  span/DOM-node approach (build icon() element + text node; can't inline <svg> into a plain
  string cleanly). Note: prior #8 progress that claimed these were done was clobber-reverted too —
  current source still shows raw emoji.
- Acceptance test "no emoji remain" fails until those are converted. Next concrete step:
  convert actIcons map to UI.icon names + render via DOM, and replace ⚠/✓ textContent prefixes
  with a small helper that prepends an icon() node.
