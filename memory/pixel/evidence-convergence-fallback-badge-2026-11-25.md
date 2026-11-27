# Pixel contribution - convergence panel fallback indicator (2026-11-25)

**Type:** idle 100% team contribution, option (b) - workflow improvement in ui/.
**Artifact:** ui/cockpit-convergence.js (edited in place, not pinned)
**What I did:** Added a visible "fallback data" badge to the convergence panel when the /api/convergence endpoint is unreachable. Previously, API failures silently showed hardcoded cycle-17 data with no indication it was stale - a data-integrity gap for a convergence dashboard.
**Change:** 3 lines added: (1) isFallback flag in refresh(), (2) badge HTML in render(), (3) pass isFallback to render(). Badge uses role="status" + aria-label for screen readers, amber color (#d4a017) matching the intervention sparkline accent.
**Verification:** bracket balance 59/59 braces, 160/160 parens, 12/12 brackets; function signature + call site confirmed via regex.
**Why new:** no fallback indicator existed before this pass (verified by reading the file pre-edit). Serves round topic: convergence metrics are only trustworthy if users know when they're looking at live vs cached data.
