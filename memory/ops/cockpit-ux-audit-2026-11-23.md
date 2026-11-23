# Fleet Cockpit UX Audit — 2026-11-23 (Designer)

Audited: `ui/cockpit.js` + injected `<style>` block. Panel is a right-slide drawer, 620px fixed, 6 sections.
All issues below are concrete and fixable in <2h total.

## P0 — Attention Hierarchy (critical alert invisible)

**Problem:** Circuit-breaker trip (`circuit.state = "MANUAL REVIEW"`) renders as a tiny red `<span>` next to the host name. A P1 incident is visually indistinguishable from normal data. In an ops cockpit, the #1 job is *pull your eye to what's wrong*.

**Fix:**
```css
/* Add to injected <style>: */
.ck-host-critical{border-left:3px solid #e554b;animation:ckpulse 1.2s ease-in-out infinite}
@keyframes ckpulse{0%,100%{opacity:1}50%{opacity:.6}}
```
In `render()` host loop, if `x.circuit` is truthy add class `ck-host-critical` to that row's `<div>`. Also prepend a `⚠` icon before the section header "Host resources" when any host is critical.

**Why:** Mirrors Grafana's alert-panel pattern — border + pulse draws peripheral vision without requiring reading text. Reference: Grafana alerting (border-left red, subtle pulse), Datadog incident banner.

---

## P1 — Keyboard Access & Dismissal

**Problem:** Panel opens on button click; only way to close is clicking the same button again. No `Escape` handler. Violates WCAG 2.1 SC 2.1.1 (Keyboard) for a modal-adjacent surface.

**Fix (3 lines in `build()`):**
```js
document.addEventListener("keydown", function(e){
  if (e.key === "Escape" && panel.classList.contains("open")) {
    panel.classList.remove("open");
  }
});
btn.setAttribute("aria-expanded", "false");
// in btn.onclick: btn.setAttribute("aria-expanded", panel.classList.contains("open"));
```

---

## P2 — Loading State (no skeleton)

**Problem:** While the first `fetch(API)` is in-flight, the panel shows "loading…" in the header and empty section headers. User sees 6 blank sections for up to 200ms+. Feels broken.

**Fix:** Add a full-panel skeleton overlay that hides on first successful render:
```css
.ck-skel{position:absolute;inset:0;background:var(--bg-1);z-index:2;display:flex;align-items:center;justify-content:center;font-size:13px;color:#8a8f98}
```
Insert `<div class="ck-skel" id="ckpSkel">Loading fleet data…</div>` as first child of panel. In `render()`: `document.getElementById("ckpSkel")?.remove();`

---

## P3 — Host Row Overflow at Narrow Widths

**Problem:** Each host row is a single flex line: `[name] [VRAM+bar] [CPU+bar] [temp+bar]`. At 620px panel width (or 100vw on mobile), the three bar groups compress and text overlaps. The `ckrow` class uses `justify-content:space-between` which doesn't wrap.

**Fix:** Change `.ckrow` for hosts to a grid with wrap:
```css
.ckhost{display:grid;grid-template-columns:auto 1fr 1fr 1fr;gap:4px 10px;align-items:center;padding:6px 0;border-bottom:1px solid #1d222b;font-size:12px}
@media(max-width:768px){.ckhost{grid-template-columns:auto 1fr 1fr}}
```
Replace the current `ckrow` div for hosts with class `ckhost`. Put name in col 1, VRAM/CPU/temp each in their own column with label above bar.

---

## P4 — Decision Log: InnerHTML Rebuild on Every Filter Keystroke

**Problem:** `paintDecs()` rebuilds the entire innerHTML of `#ckpDecList` on every keystroke in the search box. At 50 items this is fine, but the pattern will degrade if the list grows (Builder's goal says "last 50" but the API could return more). Also causes layout thrash (scroll position resets).

**Fix (low-effort):** Debounce the input handler:
```js
document.getElementById("ckpFQ").oninput = function(e){
  var v = e.target.value.toLowerCase();
  clearTimeout(window.__ckd); window.__ckd = setTimeout(function(){ decState.q = v; paintDecs(list); }, 150);
};
```
Preserve scroll: capture `box.scrollTop` before, restore after innerHTML swap.

---

## P5 — Hardcoded Colors Break Theming

**Problem:** `pctColor()`, `tempColor()`, `healthColor()` return literal hex strings. If the portal ever gets a light theme or accent-color change, these won't follow CSS custom properties.

**Fix (forward-compat):** Define thresholds as CSS custom properties and use `getComputedStyle` once at init:
```js
var cs = getComputedStyle(document.documentElement);
var C_GREEN = cs.getPropertyValue("--ok").trim() || "#2ea36b";
var C_WARN  = cs.getPropertyValue("--warn").trim() || "#d4a017";
var C_CRIT  = cs.getPropertyValue("--crit").trim() || "#e5534b";
```
Then use `C_GREEN`/`C_WARN`/`C_CRIT` in the color functions. No behavior change now, but future theming is a one-line CSS edit.

---

## P6 — Panel Width: Fixed 620px with No Resize

**Problem:** On a 1920px screen, 620px is fine. On a 1366px laptop it's 45% of viewport. No drag handle to resize.

**Fix (optional, low priority):** Add a left-edge drag strip:
```css
.ckp::before{content:'';position:absolute;left:0;top:0;bottom:0;width:5px;cursor:col-resize}
```
On mousedown, track `panel.style.width = (e.clientX - panel.getBoundingClientRect().left) + 'px'`. Clamp to 400–900px. Persist to `localStorage`.

---

## Summary Table

| # | Severity | Effort | Impact |
|---|----------|--------|--------|
| P0 | High | 15 min | Critical alerts visible at a glance |
| P1 | Medium | 5 min | Keyboard accessibility (WCAG) |
| P2 | Medium | 10 min | Perceived performance |
| P3 | Medium | 20 min | Mobile/narrow layout |
| P4 | Low | 10 min | Future-proofing + UX polish |
| P5 | Low | 15 min | Theming forward-compat |
| P6 | Low | 30 min | Power-user comfort |

Total: ~2h for all. P0+P1 should ship first (alert visibility + a11y).

---
*Auditor: Designer · File: ui/cockpit.js (full IIFE, ~180 lines) + injected style block.*