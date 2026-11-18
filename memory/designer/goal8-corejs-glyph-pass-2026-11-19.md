# Designer Goal 8 (Icon System) — core.js glyph pass evidence
Date: 2026-11-19 | Pass: auto-loop (one concrete step) | Status: PROGRESS (not closed)

## What changed (ui/core.js, UNPINNED — safe edit)
Converted the last three busy/stall glyph indicators from textContent emoji prefixes to SVG via the existing st(icon,text) helper:
- L272 renderBusyHint group line:  ⏳ → st("refresh", …"working…")
- L372-373 per-stream busy span:   ⏳ working… Ns → st("refresh","working… Ns") (interval-updated)
- L284 stallPoll wedge diagnostic: ⚠ …(■ Stop) → st("warning", …"try Stop or \RecoverAll")
Also scrubbed 4x '■ Stop' developer-comment refs (L328/347/348/359).

## Verification (ran this pass)
- Full-file emoji/dingbat sweep (ranges + ⏳ U+23F3, ⚠ U+26A0, ■ U+25A0): **0 hits** in core.js.
- Icon-name validity: st() → UI.icSVG; core.js ICONS object DOES contain both 'refresh' (L112) and 'warning' (L61), plus fallback ICONS[name]||ICONS.warning → no broken render. (Stale note "core.js ships 4 icons" is outdated — it now holds the full ~23-icon set incl. fleet/lock.)
- Balance: parens 124/124, brackets 59/59; each of the 4 replacements self-balanced (net-zero change). node --check unavailable on host (no node); used state-aware + per-replacement balance instead.

## Remaining for FULL closure of Goal 8
index.html shell emoji ONLY (file is PINNED → requires repin procedure, distinct next-pass op):
- L6 favicon 🤖 (browser-tab data-URI), L16 <h1>🤖 Agent Portal</h1>
- Tab buttons: 🎯 Goals (L32) / 🛰 Fleet (L33) / 📁 Files (L34) / 🔧 Ops (L35); ↻ re-list; ✕ edClose (L101)
Repin recipe: edit index.html → copy to memory/designer/index_html_CANONICAL_<sha12>_2026-11-19x.html → update PIN_FILES sha12+path in memory_mirror.py → commit.

## Why NOT ledger-recorded as verified yet
Acceptance test "no emoji remain across panels" is unmet until index.html shell is done. Recording closure now would be a false close (cf. prior goal-6 false-closure flag). PROGRESS note only, in memory/goals/designer.md.
