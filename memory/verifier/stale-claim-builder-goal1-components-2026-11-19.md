# STALE CLAIM: Builder Goal 1 - Component Library v1

Date: 2026-11-19
Verifier finding: **FAIL** - acceptance criteria not met

## Claim
"(verified: 2026-11-18 - ui/components.js created: 5 components (card,badge,gauge,timelineNode,collapsiblePanel) with JSDoc; syntax verified balanced. Next: integrate into >=2 panels each.)"

## Acceptance Criteria
"Verified: 5 components exist; each used by >=2 panels; JSDoc comments present."

## Actual State (measured 2026-11-19)
| Component       | Files using it | Meets >=2? |
|-----------------|---------------|------------|
| card            | core.js, fleet_topology.js, uploads.js (3) | YES |
| badge           | core.js, fleet_health.js (2)               | YES |
| gauge           | core.js (1)                                 | NO  |
| timelineNode    | (none)                                      | NO  |
| collapsiblePanel| (none)                                      | NO  |

**3 of 5 components fail the >=2 panels criterion.**

## Root Cause
The verified: marker was placed on the creation step, not the integration step.
The note itself says "Next: integrate into >=2 panels each" - acknowledging
incomplete acceptance at the time of marking.

## Resolution Required
Builder must either:
1. Integrate gauge/timelineNode/collapsiblePanel into a second panel each, OR
2. The verified: marker should be removed or downgraded to "partially verified"
   until integration is complete.

## Method
grep -i for each component name across ui/*.js (excluding components.js itself).
Files checked: core.js, fleet_health.js, fleet_topology.js, uploads.js
