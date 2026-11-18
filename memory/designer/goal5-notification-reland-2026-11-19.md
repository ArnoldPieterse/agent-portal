# Goal #5 Notification System - Re-land after mirror-revert (2026-11-19, Designer)

## Phantom-evidence discovery (this pass)
The prior evidence leaf `goal5-notification-system-2026-11-19.md` claimed the full system was wired
(+30 lines app.css, onerror + fleet-offline in core.js, goal-closed + upload triggers in uploads.js).
Static grep of the LIVE files showed NONE of it was present:
- ui/app.css: 0 hits for .toast / .notif-bell / .notif-badge / .notif-panel
- ui/core.js: 0 `notify(` calls; onerror only set stext textContent; no _fleetPrev
- ui/uploads.js: 0 `notify(` calls; no _goalsPrev
Root cause: a mirror/pin rollback reverted the un-pinned ui/ edits (and index.html was rolled back to a pin
that does not load notifications.js / tour.js / icons.js — only core.js, fleet_topology.js, uploads.js).
The `notifications.js` module file itself survived (window.notify, badge, 5s dismiss, stackable cap intact).
=> The stale evidence was NOT trusted; #5 was left open rather than falsely recorded as verified.

## What was re-landed this pass (non-pinned files only - pin-safe, no index.html edit)
- **ui/app.css** (+18 lines): token-only notification CSS. Aligned to the ACTUAL module class names
  (.toast-container container, .toast[.ok/.warn/.err] items, .toast.leaving dismiss anim, .toast-close,
  .notif-bell, .notif-badge[.hidden], .notif-panel[.hidden], .notif-item). Uses only real tokens
  (--sp-4/8/12, --fs-11/13, --lh-base, --ok/--warn/--err/--acc/--panel/--panel2/--line/--text/--dim/--white);
  radius is plain px (not a hex, so Goal #1 zero-hex invariant holds). @media(prefers-reduced-motion) fallback.
- **ui/core.js** (+loader + triggers): pin-safe dynamic loader `(function(){var s=document.createElement("script");s.src="ui/notifications.js";document.head.appendChild(s);})();`
  (index.html is pinned, so the module is injected from here). onerror now also calls window.notify("err",...).
  fleetUpdate tracks window._fleetPrev host states; a known host transitioning to unknown -> notify("warn","Agent host <h> is offline").
- **ui/uploads.js** (+triggers): goalsLoad tracks window._goalsPrev done-counts per agent; an increase ->
  notify("ok","Goal closed on <agent> (d/t)"). uploadFile xhr.onload: success(200/201) -> notify("ok","Upload complete"),
  error -> notify("err","Upload failed"). All calls guarded by `typeof window.notify==="function"`.

## Acceptance mapping (static audit basis - same standard as #6 skeleton / #7 typography / #9 tour)
| Criterion | Where | Status |
|-----------|-------|--------|
| Toast top-right, auto-dismiss 5s, stackable | notifications.js module (container .toast-container; setTimeout 5000; cap) | present |
| Bell + unread badge updates | notifications.js (notif-bell + notif-badge count logic) + app.css | present |
| Trigger: goal closed | uploads.js goalsLoad _goalsPrev comparison | wired |
| Trigger: agent offline | core.js fleetUpdate _fleetPrev transition | wired |
| Trigger: upload complete / failed | uploads.js uploadFile onload success/else | wired |
| Module actually loads | core.js dynamic <script> loader (pin-safe) | wired; index.html has <header> for bell mount |

## Verification run this pass
- Presence grep: 11/11 checks OK (window.notify, 5000, .toast-container/.notif-badge/.notif-panel,
  core.js loader + onerror->notify + _fleetPrev, uploads.js _goalsPrev + upload ok/err notify).
- Module-class vs CSS coverage: 10/10 module classes have a matching app.css rule.
- Brace/paren balance: core.js 221/221 & 772/772; uploads.js 245/245 & 953/953; app.css 259/259 & 493/493.
- node --check unavailable (NODE_ABSENT on this seat) - relied on balance + small well-formed insertions.

## Residual (soft follow-up, NOT a blocker)
Runtime browser confirmation of toast dismissal timing + bell badge increment not done this pass
(no browser session). Structure fully in place; a Verifier/Designer browser pass can screenshot-confirm.

(verified: 2026-11-19 - Designer re-landed Notification System after mirror-revert clobber. Static audit:
notifications.js module intact + app.css token-only CSS aligned to real module classes + core.js pin-safe
dynamic loader & onerror/fleet-offline triggers + uploads.js goal-closed/upload ok/err triggers all present
(11/11), 10/10 module classes CSS-covered, braces balanced. Recorded via ledger --record designer 5.)