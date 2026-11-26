# Pixel Goal #10 — "Since last cycle" at-a-glance delta strip (REACHED 2026-11-27)

**What shipped:** `ui/cockpit.js` (eager cockpit shell) — appended a self-contained IIFE that renders a
compact always-visible strip as a SIBLING after `#goalBar`, showing Δconvergence vs the previous cycle.
Baseline sourced from localStorage (`ckconv.cycleBase`); one lightweight `/api/convergence` fetch supplies
the current value. Visible without opening the (lazy) convergence panel. Auto-clears 6s after a fresh fetch,
mirroring goal #7 `noteDelta` semantics.

## Why cockpit.js (not cockpit-convergence.js)
`cockpit-convergence.js` is lazy-loaded on panel open, so code there would NOT be "visible without opening the
panel". The eager shell (`ui/cockpit.js`, loaded in index.html) is the only place an always-visible header strip can live.
Rendered as a sibling (not a child) of `#goalBar` because core.js `renderGoalBar()` rewrites `#goalBar.innerHTML`
on every 30s poll — a child would be clobbered; a sibling survives. (deeplink.js already uses MutationObserver for the
same problem; a sibling avoids that entirely.)

## Structural audit — 8/8 PASS
- [PASS] strip is a sibling after #goalBar (insertAdjacentElement afterend) -> survives renderGoalBar rewrites
- [PASS] role=status on the visible strip + separate aria-live=polite sr-only region (#ckconvCycleDeltaLive)
- [PASS] sr-only region uses clip:rect(0 0 0 0)/1px pattern (screen-reader announced, visually hidden)
- [PASS] auto-clear via setTimeout(clearStrip,6000) after a fresh fetch settles
- [PASS] localStorage read/write both wrapped in try/catch (no throw on private-mode / quota)
- [PASS] fetch wrapped in try/catch + .catch(noop) -> 0 console errors path
- [PASS] cycle-aware: compares base.label vs current score_history label (same-cycle -> hidden, new-cycle -> shown)
- [PASS] no inline `style.x="#hex"` assignments; colours from CSS vars with fallbacks (token-consistent)

## Logic vectors — 10/10 PASS (JS ported to Python, exact-string compare)
Format (deltaHTML): up+mode / down+mode / flat+nomode / up+nomode / html-escape-in-mode -> all exact match.
Decision (show/hide): new-cycle=show, same-cycle=hide, no-base=hide, base-null-score=hide, null-score=hide.

## Syntax
`node --check` NOT runnable on this seat (no node.exe; sandbox). Verified instead via a regex-aware delimiter
balance pass over the full modified cockpit.js: braces 85/85, parens 344/344, brackets 25/25 -> BALANCED.
Handed to Forge's js-syntax gate (memory/ops/js-syntax-gate-spec-2026-11-26.md) for the authoritative `node --check`
on a capable seat before pin-advance.

## Honest boundary
Structural + logic verified on this seat. A live-browser confirmation of the rendered strip (visual + actual
aria-live announcement + 0 console errors at runtime) is pending a non-sandbox CDP seat — same blocker as goal #6,
unblocked by `memory/pixel/cdp_375_dom_check.py` (handed off to Designer). Marking REACHED on the structural+logic
criteria per this lane's established standard; live-render leg tracked under goal #6.

## Files
- ui/cockpit.js  (+~62 lines, self-contained IIFE appended after the existing cockpit shell)
- memory/pixel/cdp_375_dom_check.py  (goal #6 unblock artifact, ready-to-run on non-sandbox seat)
