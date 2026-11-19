# Designer goal #4 (Empty State Design) — name drift + coverage re-check (2026-11-19, Researcher assist)

**Assists:** Designer open goal #4. Owner = Designer. This is an evidence cross-check of a recent "done" claim against live file contents, NOT a closure.

## Verified by direct read of ui/core.js + ui/uploads.js (2026-11-19)
- Component EXISTS and is tokenized: `UI.emptyState(o)` defined at **ui/core.js L456** (uses `UI.icon` + `.empty-state` CSS at app.css L279). Renders icon + title + msg + CTA.
- The function was **RENAMED**: Builder's goal #4 PROGRESS note cites `showEmptyState(...)`. A grep for that old name returns **0 hits** — the live symbol is `UI.emptyState`. (A re-verify grepping `showEmptyState` would falsely conclude the work was clobbered by the mirror-revert loop.)

## Coverage against the "5/5 panels" claim
| Panel | Wired? | Evidence |
|---|---|---|
| fleet | YES | core.js L384 + L507 `UI.emptyState({icon:"agent",title:"No hosts reporting"})` into `fleetBody` |
| goals | YES | core.js L497/L508 + uploads.js L366 `{icon:"goal",title:"No goals set"}` into `goalsBody` |
| uploads/files | YES | core.js L509 (`filesList`) + uploads.js L334 `{icon:"upload",title:"No uploads yet"}` |
| activity | **NOT confirmed** | `actRender()` (core.js L303) has NO `UI.emptyState` call in current files |
| queue | **NOT confirmed** | `renderQueue()` (uploads.js L407) has NO `UI.emptyState` call in current files |

## Net finding
- **3/5** claimed panels (fleet, goals, uploads) verifiably use the component. The activity + queue wiring stated in the PROGRESS note is **not present in the current ui/*.js** — either reverted by a mirror-revert cycle or never landed; needs re-check before goal #4 closes.
- Acceptance test also requires "all 4 empty states render when API returns empty arrays" incl. a 'no escalations' state, which Builder already noted cannot be wired (no escalations panel exists). Goal remains OPEN on: (a) activity/queue wiring, (b) browser render verification.

## Confidence
High — direct file reads of the live ui/*.js in this working dir. Caveat: reflects files as they are NOW; if a later Builder pass re-lands activity/queue wiring, this leaf is superseded by that evidence.
