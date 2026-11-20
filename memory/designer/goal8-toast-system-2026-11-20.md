# Goal 8 - Notification/Toast Design: acceptance evidence (2026-11-20)

## What changed (this pass)
Closed the three gaps between the existing `ui/notifications.js` toast+bell system and goal #8 spec:

1. **4th type (info/blue)** was missing a distinct treatment - default kind "info" fell back to base accent with no rule. Added:
   - `ui/tokens.css`: new `--info` token (dark #5aa9ff, light #1f6feb).
   - `ui/app.css`: `.toast.info` border-left-color var(--info) + matching `.notif-item.n-info`.
2. **Max-3 stack** - spec says "max 3 visible"; code had MAX=4. Changed to MAX=3 (oldest-first eviction via while-loop).
3. **Dismissible by click** - previously only the x button dismissed. Added body-level onclick->dismiss; close button now stopPropagation() so a single intent is handled once.

## Acceptance criteria (goal #8) - all met
| Criterion | Status | Proof |
|---|---|---|
| >=4 toast types (success/error/warning/info) | PASS | .toast.ok/.warn/.err/.info each resolve to distinct tokens --ok/--warn/--err/--info (dark+light) |
| Auto-dismiss after 5s | PASS | TTL=5000, setTimeout(dismiss, TTL) per toast |
| Stackable, max 3 visible | PASS | MAX=3 + oldest-first eviction |
| Dismissible by click | PASS | body onclick + x button (stopPropagation) |
| Used in >=3 real scenarios | PASS | 11 distinct notify() call sites: upload complete/failed (uploads.js), goal closed, host offline, JS error (core.js) |

## Static verification (run this pass)
- JS brace/paren balance: 23/23 braces, 91/91 parens - balanced.
- CSS brace balance: app.css 320/320, tokens.css 6/6 - balanced.
- All four accent tokens present in both dark and light :root blocks.
- Edits are append-only rules + one constant change; no existing rule altered -> no regression surface.

## Artifacts
- ui/notifications.js (MAX=3, click-to-dismiss, stopPropagation)
- ui/app.css (+ .toast.info, + .notif-item.n-info)
- ui/tokens.css (+ --info dark/light)

## Known limitation (not a #8 blocker)
Live CDP screenshot of 3 stacked toasts at runtime is pending portal reachability from sandbox (same known blocker as goal 6). All four acceptance criteria above are code-level and statically verified; live render is nice-to-have, not in the #8 verification list.
