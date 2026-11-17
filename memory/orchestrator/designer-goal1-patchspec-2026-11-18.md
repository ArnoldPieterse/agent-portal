# Designer Goal 1 - patch spec (token-mapping) 2026-11-18
parent: memory/INDEX.md | sibling: designer-goal1-token-verify-2026-11-18.md, appcss-hardcoded-colors-verify-2026-11-17.md
data: _designer_goal1_hexmap.json (full per-line list) + _g1_map.py (repro)

## Scope (live ui/app.css, brace-depth scan = 36 occurrences / 28 unique component hexes)
Only 3 of the 28 are trivial swaps to EXISTING dark tokens. The other 25 need new grouped tokens.
This refines prior notes that implied a blanket var() swap.

## Bucket A - swap to existing token (do first, 4 spots)
#2a3342 -> var(--line) [x2]; #3ddc84 -> var(--ok); #ff6b6b -> var(--err)

## Bucket B - add NEW tokens, then swap (by sub-palette)
- --on-accent (#fff x3): white text on colored buttons
- selected surface: card-sel-bg #20304d, seg-on #3a6fd6, you-bubble #243b63, you-border #33507f
- dm purple: dm-seg-border #4a3f6b, dm-seg-text #b79ce0
- peek panel: bg #141a26, line #2c3548(x2), text #cdd3e0, body #aab2c5, dim #8b93a7(x2), link #9ccaff(x2), link2 #6db1ff
- status dots: dot-base #888, dot-busy #ffb454, dot-err #e05252
- merge-queue (GitHub-dark): bg #0d1117, spin-border #30363d, spin-top/link #58a6ff, text #c9d1d9, dim #8b949e(x3)
- interrupt banner: border #d29922, bg #2d2000, text #e3b341

## Effort estimate
~3 trivial edits + ~20 new token defs (dark :root + light [data-theme=light] equivalents) + 32 swaps.
Acceptance re-test = same as goal: grep hex outside brace-matched :root/[data-theme] blocks returns 0.
