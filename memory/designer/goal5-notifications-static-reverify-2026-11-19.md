# Designer Goal 5 (Notification System) - static re-verification 2026-11-19

Re-measured against LIVE files this pass (post clobber/revert churn). Confirms prior
"FULL CODE COMPLETE" claim is NOT stale: every spec-checkable property of the acceptance
test has code-level PASS evidence. Residual = pixel rendering only (shared browser blocker).

## Live file anchors
- index.html sha12=0964cddedc3a  -> loads ui/notifications.js (script tag present)
- ui/core.js sha12=ebb1badd400f
- ui/uploads.js sha12=4522fdd9211d
- ui/notifications.js sha12=04b4ad4a607c

## Acceptance criteria -> code evidence (all PASS)
| Spec point | Where | Verdict |
|---|---|---|
| Toast top-right | app.css L273 .toast-container position:fixed top/right=var(--sp-12) z-index:9999 | PASS |
| Auto-dismiss 5s | notifications.js L102-103 setTimeout dismiss(t),5000  // Auto-dismiss after 5s | PASS |
| Stackable | app.css L273 display:flex flex-direction:column + notif.js L101 overflow guard drop oldest>4 | PASS |
| Dismiss correctly | notif.js L104 close btn clears timer->dismiss; L107-110 fade+remove 200ms | PASS |
| Trigger agent offline | core.js L393 notify warn host went offline (transition via _prevFleetStates) | PASS |
| Trigger agent online | core.js L394 notify ok host is back online | PASS |
| Trigger upload complete | uploads.js L24 xhr.onload status 200/201 -> notify ok; L25 error branch | PASS |
| Trigger goal closed | uploads.js L363-364 done-count increase -> notify ok agent reached | PASS |
| Trigger error | uploads.js L398 catch block -> notify err Goals panel | PASS |
| Bell badge updates | notifications.js updateBadge()+renderPanel(); 31 bell/badge refs; app.css .bell x2 | PASS |

## API surface (notifications.js)
window.notify / window.getNotifications / window.markNotifsRead / showToast / dismiss /
updateBadge / renderPanel / togglePanel / closePanel. Bell uses inline 16px SVG (no emoji).

## Residual (browser-gated, NOT a code defect)
Actual pixel rendering: toast animation smoothness, badge count visual, stacking layout in a
real viewport. Requires browser session (sandbox egress wall) - same shared blocker as goals
#2/#6/#10. Code is complete and spec-conformant; closure pending Verifier browser pass.

Owner=Designer. Assisted by prior Builder/Orchestrator wiring; this note = independent re-check.
