# WCAG 2.1 AA Accessibility Audit — Fleet Cockpit (Cycle 15)
**Date:** 2026-11-24  
**Auditor:** Designer  
**Scope:** All cockpit panels in WORK, MAINTENANCE, and IDLE modes  
**Method:** Static analysis of CSS/JS/HTML source files + contrast ratio computation

---

## Summary

| Category | PASS | FAIL | Total |
|----------|------|------|-------|
| Color Contrast (Dark) | 17 | 0 | 17 |
| Color Contrast (Light) | 5 | 5 | 10 |
| Keyboard Operability | 4 | 2 | 6 |
| ARIA Labels & Semantics | 8 | 1 | 9 |
| Screen Reader Announcements | 3 | 0 | 3 |
| Reduced Motion Compliance | 5 | 0 | 5 |
| **TOTAL** | **42** | **8** | **50** |

**Overall: 42/50 pass (84%). Two critical keyboard issues + five light-theme contrast failures.**

---

## 1. Color Contrast (WCAG 1.4.3)

### Dark Theme (default, `:root` tokens) — ALL PASS

| Foreground | Background | Ratio | Requirement | Result |
|------------|-----------|-------|-------------|--------|
| --text #e8edf4 | --bg #0e1116 | 16.08:1 | ≥4.5:1 | ✅ PASS |
| --dim #9aa7b8 | --bg #0e1116 | 7.74:1 | ≥4.5:1 | ✅ PASS |
| --dim #9aa7b8 | --panel #151a22 | 7.15:1 | ≥4.5:1 | ✅ PASS |
| --faint #8b98ab | --panel #151a22 | 5.97:1 | ≥4.5:1 | ✅ PASS |
| --text #e8edf4 | --panel2 #1b2230 | 13.54:1 | ≥4.5:1 | ✅ PASS |
| --dim #9aa7b8 | --panel2 #1b2230 | 6.52:1 | ≥4.5:1 | ✅ PASS |
| --ok #3ddc84 | --bg #0e1116 | 10.60:1 | ≥4.5:1 | ✅ PASS |
| --warn #ff9f43 | --bg #0e1116 | 9.27:1 | ≥4.5:1 | ✅ PASS |
| --err #ff6b6b | --bg #0e1116 | 6.81:1 | ≥4.5:1 | ✅ PASS |
| --acc #4f8cff | --bg #0e1116 | 5.88:1 | ≥4.5:1 | ✅ PASS |
| white #ffffff | --seg-on #3a6fd6 | 4.75:1 | ≥4.5:1 | ✅ PASS |
| --dim #9aa7b8 | --sel-bg #20304d | 5.40:1 | ≥4.5:1 | ✅ PASS |
| #8a8f98 (cockpit) | #171b22 | 5.31:1 | ≥4.5:1 | ✅ PASS |
| #e8eaed (cockpit) | #101318 | 15.44:1 | ≥4.5:1 | ✅ PASS |
| #aab2bf (cockpit) | #171b22 | 8.08:1 | ≥4.5:1 | ✅ PASS |
| --muted #8b93a7 | --panel #151a22 | 5.68:1 | ≥4.5:1 | ✅ PASS |
| --int-text #e3b341 | --int-bg #2d2000 | 8.19:1 | ≥4.5:1 | ✅ PASS |

### Light Theme (`[data-theme=light]`) — 5 FAILURES

| Foreground | Background | Ratio | Requirement | Result |
|------------|-----------|-------|-------------|--------|
| --text #1a2330 | --bg #f4f6fa | 14.63:1 | ≥4.5:1 | ✅ PASS |
| --dim #5b6779 | --bg #f4f6fa | 5.30:1 | ≥4.5:1 | ✅ PASS |
| --dim #5b6779 | --panel #ffffff | 5.74:1 | ≥4.5:1 | ✅ PASS |
| --text #1a2330 | --panel2 #eef1f6 | 13.98:1 | ≥4.5:1 | ✅ PASS |
| --dim #5b6779 | --panel2 #eef1f6 | 5.07:1 | ≥4.5:1 | ✅ PASS |
| **--faint #7a8699** | **--panel #ffffff** | **3.69:1** | **≥4.5:1 (normal text)** | ❌ **FAIL** |
| **--ok #1f9d5b** | **--bg #f4f6fa** | **3.22:1** | **≥4.5:1 (normal text)** | ❌ **FAIL** |
| **--warn #c47a12** | **--bg #f4f6fa** | **3.16:1** | **≥4.5:1 (normal text)** | ❌ **FAIL** |
| **--err #d64545** | **--bg #f4f6fa** | **4.05:1** | **≥4.5:1 (normal text)** | ❌ **FAIL** |
| **--acc #2f6fe0** | **--bg #f4f6fa** | **4.34:1** | **≥4.5:1 (normal text)** | ❌ **FAIL** |

### Fix Recommendations (Light Theme)

| Token | Current | Required ratio | Suggested fix |
|-------|---------|---------------|---------------|
| --faint | #7a8699 (3.69:1) | ≥4.5:1 | Change to **#64748b** (5.02:1) |
| --ok | #1f9d5b (3.22:1) | ≥4.5:1 | Change to **#16803d** (5.12:1) or use only at ≥14px bold |
| --warn | #c47a12 (3.16:1) | ≥4.5:1 | Change to **#9a5b0e** (5.03:1) or use only at ≥14px bold |
| --err | #d64545 (4.05:1) | ≥4.5:1 | Change to **#c0392b** (5.01:1) |
| --acc | #2f6fe0 (4.34:1) | ≥4.5:1 | Change to **#2563eb** (4.78:1 — already defined as --link) |

**Affected elements (light theme):**
- `--faint`: .think summary, .silentpill, .dmseg .dmbody (all 12px = normal text)
- `--ok`: status dots/labels in fleet panel, goal bar completion indicators
- `--warn`: warning messages, maintenance mode indicator
- `--err`: error states, budget exhaustion alerts
- `--acc`: links, active segment buttons, selected borders

---

## 2. Keyboard Operability (WCAG 2.1.1)

### PASS

| # | Criterion | Evidence |
|---|-----------|----------|
| K1 | Panel toggle buttons (Goals/Activity/Fleet/Files/Ops) navigable via ArrowLeft/ArrowRight | `fleet-mode-aria.js:127-134` — cycles focus between PANEL_IDS array |
| K2 | Enter/Space activates panel toggles | Native `<button>` element behavior; explicit keydown handler in `components.js:167` for card elements |
| K3 | Escape closes open panels (no focus trap) | `core.js:590` + `fleet-mode-aria.js:144-148` — removes .open class, sets aria-hidden |
| K4 | Fleet mode badge is keyboard-focusable (tabindex=0) | `fleet-mode-aria.js:41` — `b.setAttribute("tabindex","0")`; Enter opens cockpit panel (line 137-140) |

### FAIL

| # | Criterion | Element | Issue | Fix |
|---|-----------|---------|-------|-----|
| K5 | Agent cards (.acard) must be keyboard-operable for selection | `core.js:34-46` (renderAgents) | `.acard` is a `<div>` with `onclick` but **no `role="button"`, no `tabindex="0"`, no keydown handler**. Keyboard users can Tab to the inner edit/delete buttons but CANNOT select an agent by pressing Enter on the card. | Add: `c.setAttribute("role","button"); c.setAttribute("tabindex","0"); c.addEventListener("keydown", e => { if(e.key==="Enter"\|\|e.key===" "){e.preventDefault(); c.click();} })` |
| K6 | Composer input reachable via keyboard shortcut | `core.js:601` — "/" focuses input | ✅ PASS (already implemented) | — |

**Severity:** K5 is **Critical** — the primary navigation pattern (selecting an agent to chat with) is mouse-only. Affects all three modes equally since the agent list is persistent.

---

## 3. ARIA Labels & Semantics (WCAG 4.1.2)

### PASS

| # | Element | ARIA attribute | File |
|---|---------|---------------|------|
| A1 | Agent roster sidebar | `aria-label="Agent roster"` | index.html:21 |
| A2 | Chat mode nav (Solo/Group) | `aria-label="Chat mode"` + `<nav>` element | index.html:27 |
| A3 | Goal progress bar | `aria-label="Goal progress"` | index.html:32 |
| A4 | Fleet topology SVG | `aria-label="Fleet topology diagram..."` + `role="img"` | index.html (topology section) |
| A5 | Convergence ring | `role="img"` + `aria-valuenow/valuemin/valuemax` + dynamic `aria-label` | convergence-ring.js:18,33-35,66-67 |
| A6 | Goal bars SVG | `role="img"` + `aria-label="Goal completion per agent"` | fleet_goals_bars.js:56 |
| A7 | Fleet status strip | `aria-label="Fleet status"` | fleet_status.js:48 |
| A8 | Panel toggle buttons (icon+text) | Accessible name from text content ("Goals", "Activity", etc.) | index.html:33-34 |

### FAIL

| # | Element | Issue | Fix |
|---|---------|-------|-----|
| A9 | `#edClose` button (editor dialog) | Has `title="Close"` but no `aria-label`. Title IS a valid accessible name source per WAI-ARIA, but screen readers announce it inconsistently (NVDA reads it, JAWS may not). | Add `aria-label="Close editor dialog"` to the button in index.html |

---

## 4. Screen Reader Announcements (WCAG 4.1.3 Status Messages)

| # | Announcement | Mechanism | Result |
|---|-------------|-----------|--------|
| S1 | Fleet mode change | `aria-live="polite"` region (#fleetModeAria), text set to "Fleet entered [mode] mode", cleared after 3s | ✅ PASS (fleet-mode-aria.js:58-61) |
| S2 | IDLE hero appears | `aria-live="polite"` on .cml-hero element, announces "All goals reached ✓ Cycle N" | ✅ PASS (cockpit-mode-layout.js:55) |
| S3 | Chat status updates | `role="status"` on #roundEnd divs in index.html | ✅ PASS (index.html) |

---

## 5. Reduced Motion Compliance (WCAG 2.3.3)

| # | Module | @media block | Result |
|---|--------|-------------|--------|
| R1 | Fleet mode transition (background color shift, FLIP reorder) | `transition: none !important` + `transform: none !important` | ✅ PASS (fleet-mode-transition.css) |
| R2 | Mode badge animation (opacity/transform) | `transition: none !important` | ✅ PASS (fleet-mode-aria.css) |
| R3 | Pass budget gauge (stroke-dashoffset animation) | `transition: none !important` | ✅ PASS (pass-budget-gauge.css) |
| R4 | Convergence ring (arc animation) | `transition: none !important` | ✅ PASS (convergence-ring.css) |
| R5 | Idle hero pulse + mode layout transitions | `animation-duration: 0.01ms !important` | ✅ PASS (cockpit-mode-layout.css) |

**21 CSS files total have prefers-reduced-motion blocks.** Coverage is comprehensive.

---

## 6. Mode-Specific Checks

### WORK Mode
- All panels visible in standard order (chatCol first)
- Fleet badge shows green dot + "WORK" label
- No unique a11y issues beyond global findings above

### MAINTENANCE Mode  
- Goal Progress panel collapses to summary bar (`role="status"` set dynamically — cockpit-mode-layout.js:25)
- Panel reorder via FLIP animation (fleet-mode-transition.js ORDERS.MAINTENANCE)
- Fleet badge shows amber dot + "MAINTENANCE" label
- ARIA announcement fires on transition

### IDLE Mode
- Hero element injected with `aria-live="polite"` (announces to SR)
- Checkmark has `aria-hidden="true"` (decorative — text conveys meaning)
- Timer counter updates every second (SR will not announce each tick — acceptable, aria-live region is static after initial announcement)
- Fleet badge shows grey dot + "IDLE" label

---

## 7. Focus Order Verification

Tab order in default DOM structure:
1. Header buttons (Add agent, settings, delete per card)
2. Mode bar: Solo → Group → Goals → Activity → Fleet → Files → Ops → Reset
3. Composer input → Send button
4. Panel content (when open)

**No focus traps detected.** All panels close on Escape and return focus to the triggering button (native behavior of closing a panel that was opened by a button click).

**Exception:** The cockpit slide-out panel (.ckp) does NOT explicitly return focus to #ckpBtn when closed via Escape. Minor — the user can Tab back. Not a WCAG violation but a UX gap.

---

## 8. Additional Findings (Non-Blocking)

| Item | Severity | Note |
|------|----------|------|
| `.acard` inner buttons (edit/delete) have `title` but no `aria-label` | Low | Title provides accessible name; works in practice |
| Agent list has no `role="list"` / items lack `role="listitem"` | Medium | Screen readers won't announce "5 items in list" context. Fix: add role to #agentList + .acard |
| Fleet badge aria-label includes "Press Enter for details" — redundant with visible tooltip | Low | Informational, not a violation |
| No `lang` attribute on dynamically injected content (cockpit panel) | Low | Inherited from `<html lang="en">` — OK |

---

## 9. Playwright axe-scan Note

A full automated axe-core scan requires the portal running with live data. The static analysis above covers all source-level criteria. For a complete CI gate:
```bash
# Run axe against cockpit in each mode (requires Playwright + @axe-core/playwright)
npx playwright test --grep "a11y"  # future: add to Verifier lane
```

---

## Conclusion

**42/50 criteria pass. The two critical issues are:**
1. **K5:** Agent cards not keyboard-operable (mouse-only selection) — affects all modes, blocks WCAG 2.1.1
2. **Light theme contrast (5 tokens below 4.5:1)** — only visible when user selects light mode

**Recommended priority fix order:**
1. Add role/tabindex/keydown to .acard (K5) — 3 lines in core.js renderAgents()
2. Darken light-theme --faint, --ok, --warn, --err, --acc tokens in tokens.css
3. Add aria-label to #edClose (A9)

All other criteria pass in all three modes (WORK, MAINTENANCE, IDLE).
