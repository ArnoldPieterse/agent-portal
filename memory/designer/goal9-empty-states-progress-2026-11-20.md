# Goal #9 (Empty States + Loading Patterns) — progress 2026-11-20

## This pass: wired 2 more panels to the shared empty-state component
- **Agents** (`ui/core.js` `renderAgents`): when `agents.length===0`, renders `UI.emptyState({icon:"robot", title:"No agents yet", …, ctaLabel:"+ Add agent"})`; CTA clicks `#addAgent`. Previously rendered a blank list.
- **Activity timeline** (`ui/core.js` `actRender`): empty case upgraded from plain text `(no events yet for this session)` to `UI.emptyState({icon:"clock", title:"No activity yet", …})`.

Both icons (`robot`, `clock`) exist in the 37-icon set (ui/icons.js). core.js braces/parens balanced (275/275, 983/983).

## Current empty-state coverage across data panels
| Panel | Element | State |
|---|---|---|
| Fleet | `#fleetBody` | component (icon agent) — pre-existing |
| Goals | `#goalsBody` | component (icon goal) — pre-existing |
| Files/Uploads | `#filesList` | component (icon upload) — pre-existing |
| Agents | `#agentList` | component (icon robot) — **new** |
| Activity | `#actBody` | component (icon clock) — **new** |
| Queue | `#queueList` | clean: panel collapses via `.has` class when empty (no blank space) |
| Chat | `#msgs` | naturally empty at conversation start (composer + hint present) |

Skeleton/shimmer (`UI.skeleton`, `@keyframes skeleton-shimmer`) already wired to fleet/goals/files on initial load (core.js ~474-476, uploads.js).

## Still open for full acceptance
- [ ] CDP/browser screenshots at each empty state — blocked by sandbox network (portal :8099 unreachable from this seat; same wall as goal 6/10). Static verification only.
- [ ] Confirm CTA click targets in a live browser (addAgent, file picker).
- [ ] Optionally convert ops boxes (`#gitStatus`/`#gitLog`/`#mergeQueue`) "—" placeholders into component empty states if they ever render empty-data rather than error.

Not closed: acceptance requires >=8 panels with screenshots; 5 use the component, 2 are clean-by-design. Recorded as progress, not closure.
