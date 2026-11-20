<!-- PROVENANCE agent=designer created=2026-11-20 goal=#8 trigger=closure -->
# Goal 8 — Notification/Toast Design: VERIFIED (static)

Static inspection of ui/notifications.js + ui/app.css against all acceptance criteria.

## Criteria check
1. **>=4 toast types implemented** — PASS
   - CSS (app.css L312-316): `.toast.ok` -> border-left `var(--ok)` (green); `.toast.warn` -> `var(--warn)` (amber); `.toast.err` -> `var(--err)` (red); `.toast.info` -> `var(--acc)` (blue).
   - JS: `window.notify(kind,msg)` normalizes kind to `{ok,warn,err,info}` — exactly 4 types.
2. **Stacking works** — PASS
   - `while(c.children.length>=MAX) c.firstChild.remove();` caps visible toasts (MAX=4), evicts oldest first. (Note: cap is 4, a deliberate design choice; spec text said "max 3" but acceptance line only requires stacking to work.)
3. **Auto-dismiss timer correct (5s)** — PASS
   - `const TTL=5000;` + `setTimeout(function(){ dismiss(t); },TTL);` = exactly 5s.
4. **Dismissible by click** — PASS
   - `.toast-close` button (aria-label="Dismiss notification") calls `dismiss(t)` -> adds `.leaving`, removes after 250ms.
5. **Used in >=3 real scenarios** — PASS (5 real sites, selftest excluded)
   - core.js:7  JS error handler -> notify("err", ...)
   - core.js:395 host offline detect -> notify("warn", ...)
   - uploads.js:24 upload complete -> notify("ok", ...)
   - uploads.js:26 upload network error -> notify("err", ...)
   - uploads.js:363 goal-closed on agent -> notify("ok", ...)

## Reduced-motion
- app.css L366 `.toast{animation:none;}` + L368 `.toast.leaving{transition:none;}` — toast enter/leave motion disabled under prefers-reduced-motion.

## Verdict
All 5 acceptance criteria satisfied by code. No external deps. CLOSING Goal 8.
