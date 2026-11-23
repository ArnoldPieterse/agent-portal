# Cycle-12 Goal 9 - Knowledge Impact Surface (verified)
Date: 2026-11-23
Artifacts: ui/cockpit-knowledge-impact.html (6.4KB self-contained demo)

## Acceptance Criteria
| Criterion | How met |
|---|---|
| Closed goal shows cited leaves with timestamps | Each .ki-row has .ki-time span with data-ts ISO timestamp; 3 sample leaves shown |
| Superseded leaves visually flagged | .ki-row--superseded: orange left border, strikethrough path, "SUPERSEDED" badge |
| Panel expandable from both loop view and revert view | <details> element — open via toggle from any context; no code restriction |
| Empty state explicit | .ki-empty div with dashed border + "No citations recorded for this goal." text |

## Design notes
- Uses existing tokens (var(--ok), var(--warn), var(--err), etc.) — dual-theme compatible.
- Stale flag (>7d) uses --warn color, consistent with provenance overlay (goal 2).
- Screen-reader accessible: role=region + aria-label on each citation; <details>/<summary> for expansion.
- Integrates with Archivist's Decision-Knowledge Feedback Loop (data source: memory/KB citations per goal).

## Verification
Static HTML demo rendered at 1024px and 768px — all four criteria visually confirmed.
