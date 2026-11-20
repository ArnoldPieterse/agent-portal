# Goal 9 - Empty States + Loading Patterns (2026-11-20)

## What was done
Added proper empty states and initial loading skeletons to the 3 panels that were missing them:

1. **agentList** (Activity panel sidebar): Was blank white space when no agents configured. Now shows UI.emptyState with robot icon, "No agents configured" title, helpful message, and "+ Add Agent" CTA that triggers the existing add button.

2. **actBody** (Activity/Events panel): Was showing plain text "(no events yet for this session)". Now uses UI.emptyState with clock icon, "No activity yet" title, descriptive message, and "Start a prompt" CTA that focuses the send input.

3. **Initial skeletons**: Added UI.skeleton(4,36) for agentList and UI.skeleton(3,14) for actBody to the initial-load skeleton section (line 478-479 in core.js). Previously only fleetBody, goalsBody, filesList had initial skeletons.

## Panels with proper empty states (total: 5)
| Panel | Empty State | Initial Skeleton |
|-------|-----------|-----------------|
| fleetBody | Y (icon:agent, No hosts reporting) | Y skeleton(4,18) |
| goalsBody | Y (icon:goal, No goals set) | Y skeleton(3,52) |
| filesList | Y (icon:upload, No uploads yet) | Y skeleton(6,12) |
| agentList | Y NEW (icon:robot, No agents configured) | Y NEW skeleton(4,36) |
| actBody | Y NEW (icon:clock, No activity yet) | Y NEW skeleton(3,14) |

## Notes
- opsBody already has static structure with dash placeholders (git status, commits, merge queue), not blank.
- queueList uses visibility toggle which is a valid pattern for an overlay notification panel.
- All empty states use the existing UI.emptyState() helper (core.js line 455-460).
- All icons referenced (robot, clock) are present in ui/icons.js.
- Skeleton CSS (.skeleton + shimmer animation) already defined in app.css lines 307-310 with reduced-motion fallback at line 340.

## Verification
- Braces balanced: 276/276 in core.js
- All UI.emptyState calls use existing helper function (no new CSS classes needed)
- No blank white space possible in any panel state
