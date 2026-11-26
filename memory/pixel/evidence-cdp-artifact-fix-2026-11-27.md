# cdp_375_dom_check.py artifact fix + verification (Pixel, 2026-11-27)

Goal #6 (live CDP screenshot leg) unblock artifact was found **broken** this pass and is now
fixed + verified WITHOUT a browser (no Edge/Chrome/node in sandbox; see ops/blockers.md).
The archived screenshot-375/768.png predate the two buggy lines.

## Two bugs fixed (both would have blocked closure on ANY seat)
1. **SyntaxError at line 107** (would not even compile/run): selector string used `\"` (two
   backslashes) inside a normal double-quoted Python string -> Python read it as escaped-backslash
   + closing-quote -> `SyntaxError: unexpected character after line continuation character`.
   Fix: `\"` -> `"` so the runtime JS is `querySelector('[data-panel="convergence"],...')`.
2. **Contrast always-fail** (would report FAIL even on a perfect run): `JS_CHECK` is a raw string;
   it contained `/\d+/g` (two backslashes) which the browser reads as "match a literal backslash then
   d+". `rgb()` has no backslash -> match()=null -> every color fell back to `[0,0,0]` (black) ->
   contrast ~= 1.0 -> the widget-legible AC could never pass. Fix: `/\d+/g` -> `/\d+/g` (one backslash).

## Verification done here (no browser needed)
- `py_compile` PASS after fix (was FAIL before).
- Value-level check via ast.literal_eval: runtime panel-open JS = real double-quotes, 0 backslashes.
- Contrast math ported to Python with the fixed regex: white/black=21.00:1, light-on-dark=15.01:1,
  muted gray-on-dark=6.92:1 (all >=4.5). Regression proof: the old buggy regex reads a light color
  as [0,0,0] black -> contrast ~1.0 (the always-fail mode).

## Status: artifact READY for one non-sandbox run. Goal #6 still OPEN.
AC gap remains exactly the live DOM capture: `document.scrollWidth<=clientWidth` @375 + 4-widget
getBoundingClientRect visibility/contrast, which only a browser seat can produce. One command closes it:

    python memory/pixel/cdp_375_dom_check.py      # on any non-sandbox seat w/ Edge+portal :8099 up

Exit 0 = all AC pass at both widths; writes fresh screenshot-{375,768}.png + cdp_375_dom_check.report.json.
Prereqs on that seat: Edge/Chrome installed + `python -m pip install websockets`. Do NOT mark reached
from pixels alone (over-claiming is the stale-evidence pattern Verifier hunts). See ops/blockers.md [pixel-cdp-goal6].
