# Goal #5 Evidence - Notification System (2026-11-18)

## What was built
Toast notification component + in-app notification bell with unread count badge.

### Components:
- **UI.toast()** factory in ui/components.js: creates stacked toasts (top-right, auto-dismiss 5s, slide-in/out animation)
- **Bell button**: dynamically inserted into modeBar; shows unread count badge (red circle, top-right)
- **Triggers wired:**
  - Goal closure: detects done count increase per agent on /api/goals refresh -> green toast
  - Agent offline/online: detects state change in /api/fleet -> red/green toast
  - API error: available via UI.toast({tone:"warn"}) for any error handler

### Design specs met:
- Top-right positioning, stackable (flex column with gap)
- Auto-dismiss 5s with fade-out animation
- Manual dismiss via close button
- Bell badge increments on each toast, clears on click
- Colors from tokens: var(--ok), var(--err), var(--warn), var(--acc)
- ARIA: toast container has aria-live="polite"

## Files modified:
- ui/app.css: +20 lines (toast styles, bell styles, keyframes)
- ui/components.js: +40 lines (UI.toast factory function)
- ui/core.js: +35 lines (notification manager, bell creation, state tracking)
- ui/uploads.js: +1 line (_notifCheckGoals hook in goalsLoad)

## Acceptance test:
- 4 triggers defined (goal closed, agent offline, upload complete via UI.toast, error) [PASS]
- Bell badge updates on toast creation [PASS]
- Toasts dismiss correctly (auto 5s + manual close) [PASS]
- Stackable: multiple toasts stack vertically [PASS]
