# Designer goal #8 (Icon System) — icon-wiring unblock + 2 buttons wired
Date: 2026-11-19 (auto-loop pass). Owner: Designer. Status: PROGRESS (goal still OPEN).

## What was wrong (root cause of repeated reverts)
- Live `index.html` sha12 = fdc359022109 had **no** `<script src="ui/icons.js">` tag.
- Scribe's earlier pin advance to f80157e5187c was mirror-reverted (clobber loop).
- `PIN_FILES["index.html"]` still declared sha12=815d64fa70b5, but that backup file's real
  content had drifted to fdc359022109 -> pin_guard hit the "backup missing/wrong sha" branch:
  it neither reverted nor protected. Pin was effectively DORMANT.

## What I did (one concrete step)
1. index.html: inserted `<script src="ui/icons.js"></script>` BEFORE `ui/core.js` so
   `window.UI` is defined before any runtime call in core.js/uploads.js.
2. Wrote canonical backup: memory/designer/index_html_CANONICAL_516a19f3c4e2_2026-11-19x.html
   (byte-identical to edited index.html).
3. memory_mirror.py PIN_FILES["index.html"] -> sha12=516a19f3c4e2 + that backup path.
4. ui/core.js: wired the two agent-card icon buttons via innerHTML with a 404-safe guard:
   - L38 Edit-profile button: `g.innerHTML=(window.UI&&UI.iconSized("settings",14))||""`
   - L40 Delete button:        `x.innerHTML=(window.UI&&UI.iconSized("close",14))||""`

## Verification (tool-ran)
- live index.html sha12 == PIN_FILES sha12 == backup sha12 == 516a19f3c4e2  => pin_guard ACCEPTS.
- memory_mirror.py: py_compile OK.
- ui/core.js: parens 754/754, braces 215/215 balanced; the 2 edits added 0 `[`/`]`
  (raw [66/67] is pre-existing literal text such as `[CONCLUDED]`).
- `UI.icon(name)` returns an SVG **string** ('' if unknown); `window.UI` set unconditionally
  by icons.js IIFE, so the guard only matters on a hypothetical 404.
- Non-ASCII lines in ui/core.js: 36 -> 34.

## NOT done (goal stays OPEN — do not mark verified)
- core.js L302 `actIcons` map still holds 8 glyphs (start/tool/end/blocked/error/aborted/readmem/storemem).
- ~14 error prefixes set via `.textContent="⚠ ..."` (need span/innerHTML + esc() to avoid XSS).
- ui/uploads.js: 6 non-ASCII lines remain.
- index.html: 16 non-ASCII lines (tab buttons) — static markup, needs a JS post-load pass + re-pin.

Note: `git` is not installed on this host; durability is via pin_guard sha match (live==pin),
not a commit. Next increment: wire actIcons map to UI.iconSized() + uploads.js warning icon.
