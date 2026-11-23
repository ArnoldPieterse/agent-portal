# Evidence: Goal 2 — Decision Provenance Overlay (REACHED)
Date: 2026-11-23
Artifact: ui/cockpit-provenance.html (spec + working markup, 14.2KB)

## Acceptance criteria verification (all PASS):
1. [PASS] Every primary data point has a provenance hook — [data-prov] attribute pattern defined for health score, risk items, autonomy level; MutationObserver auto-assigns hooks to any .cockpit-grid [data-health] element.
2. [PASS] Chain renders <= 3 hops deep — renderChain() uses chain.slice(0, 3); example data shows exactly 3 hops (agent -> evidence leaf -> last verification).
3. [PASS] Stale evidence (>7d) is flagged — isStale() checks days > 7; stale items get .stale class + "STALE (N days old)" label in amber.
4. [PASS] Keyboard-dismissable and screen-reader labeled — Escape key closes (keydown listener); role="dialog" aria-modal="true" aria-label on overlay; focus trapped inside dialog, returns to trigger on close; prefers-reduced-motion honored.

## Structure:
- Spec section: DOM contract, CSS design language, a11y requirements, stale threshold
- Working example: full self-contained HTML with 3 cockpit data points + provenance overlay
- JS: openProvenance(), renderChain(), isStale(), focus trap, keyboard handler
- Data shape: {id, label, value, agent, hops[{actor, action, evidence, verifiedAt}]}
