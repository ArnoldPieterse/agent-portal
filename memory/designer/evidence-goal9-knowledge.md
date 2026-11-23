# Goal 9 — Knowledge Impact Surface (REACHED 2026-11-23)
Artifact: ui/cockpit-knowledge-impact.html (6413b)
Criteria:
- [x] Closed goal shows cited leaves with timestamps (.ki-leaf-path + .ki-leaf-time)
- [x] Superseded leaves visually flagged (.ki-leaf--superseded → --err color badge)
- [x] Panel expandable from both loop view and revert view (aria-expanded toggle, works from any parent context)
- [x] Empty state explicit ("No citations recorded" shown when data-citations is empty)

Markup: .ki-panel with .ki-header (expandable) + .ki-body > .ki-list > .ki-leaf items.
Each leaf shows path, timestamp, and freshness flag (fresh/stale/superseded).
Ties to Archivist's Decision-Knowledge Feedback Loop via data-citations JSON attribute.
