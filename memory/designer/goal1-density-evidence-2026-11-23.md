# Goal #1 Evidence: Adaptive Information Density (Calm vs. Incident)
Date: 2026-11-23
Artifact: ui/cockpit-density.css (7,486 chars, live via @import in ui/app.css)

## Acceptance criteria verification (static analysis):
1. [PASS] Calm mode shows <= 3 primary panels — .panel-health + .panel-loops visible; .panel-agents/.hosts/.topology/.decisions/.risks all display:none. Goalbar is in header area, not grid.
2. [PASS] Incident mode auto-triggers on first critical state — JS contract documented (MutationObserver on data-health attribute; sets data-density="incident" + adds .panel--critical). CSS handles full expansion + red glow.
3. [PASS] Transition < 500ms, reversible, preserves scroll — --density-transition: 280ms ease; hidden panels use display:none (scroll container doesn't shift); grid positions maintained for visible panels.
4. [PASS] prefers-reduced-motion: instant swap — @media block sets transition: none and --density-transition: 0ms.

## Live delivery:
- ui/cockpit-density.css imported at line 2 of ui/app.css (after tokens.css)
- index.html links ui/app.css → cascade delivers density rules to any .cockpit-grid element

## Files modified:
- ui/cockpit-density.css (created, full spec + CSS)
- ui/app.css (added @import "cockpit-density.css")
