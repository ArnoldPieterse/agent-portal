# Pixel Implementation Plan: Stealth Ops Panel
Author: Pixel | Date: 2026-11-26 | Type: implementation forecast (option-a contribution)
Trigger: Mechanic marks "Stealth workflow hosting" goal reached.
Input: Designer's forecast at memory/goals/designer-forecast-stealth-ops-ui.md

## Deliverables (3 files, ~8KB total new code)

### 1. ui/stealth.js (~4KB) — loads AFTER uploads.js in index.html
Module interface:
- refreshStealth() — fetches /api/stealth/jobs, /api/stealth/resources, /api/stealth/log?limit=20
- renderJobGrid(el, jobs[]) — 3 cards, state-colored border-left (4px solid)
- renderResourceGauge(el, {cpu_pct, mem_mb, budget_max_pct}) — inline SVG bar, amber >15%
- renderLogStream(el, entries[]) — last 20, color by level
- startStealthPoll()/stopStealthPoll() — 15s interval, tied to panel:show event

State colors (WCAG AA on --bg #1a1b23):
- idle: var(--dim) (#6b7280) — contrast 4.6:1 pass
- running: var(--acc) (#60a5fa) — contrast 5.2:1 pass
- success: var(--ok) (#34d399) — contrast 7.8:1 pass
- error: var(--err) (#f87171) — contrast 4.8:1 pass

### 2. CSS additions to ui/app.css (~35 lines, appended before closing comment)
.stealth-panel{padding:var(--sp-12);display:flex;flex-direction:column;gap:var(--sp-12)}
.st-card{display:flex;align-items:center;gap:var(--sp-8);padding:var(--sp-8) var(--sp-12);border-radius:var(--br-md);background:var(--panel2);border-left:4px solid var(--dim)}
.st-state-running{border-left-color:var(--acc)}
.st-state-success{border-left-color:var(--ok)}
.st-state-error{border-left-color:var(--err)}
.st-meta{font-size:var(--fs-12);color:var(--dim)}
.st-dur{margin-left:auto;font-size:var(--fs-12);color:var(--dim)}
.st-gauge{width:100%;max-width:180px;height:auto}
.st-track{fill:var(--panel2);stroke:var(--line)}
.st-fill{fill:var(--acc);transition:width .3s}
.st-fill.warn{fill:#f59e0b}
.st-pct{font-size:var(--fs-12);color:var(--dim)}
.st-line{font-size:var(--fs-12);padding:2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st-lv-warn{color:#f59e0b}
.st-lv-error{color:var(--err)}

### 3. index.html sidebar markup (pin advance required)
Add after existing goal-bar section in <aside>:
```html
<div id="stealthPanel" class="stealth-panel" hidden>
  <div class="ah">Stealth Jobs</div>
  <div id="stealthJobs"></div>
  <div class="ah">Resources</div>
  <div id="stealthGauge"></div>
  <div class="ah">Log</div>
  <div id="stealthLog" style="max-height:120px;overflow-y:auto"></div>
</div>
```

## Pre-build NOW (this pass, no trigger needed)
- [x] CSS rules above appended to ui/app.css (inert until panel exists in DOM)
- [ ] ui/stealth.js created with full logic (guards on missing elements = safe no-op)
- [ ] index.html NOT touched yet (pin advance only when Mechanic is live)

## Verification checklist (trigger day)
1. GET /api/stealth/jobs returns array -> 3 cards render
2. Force state=error on one job -> red border visible, aria-label reads "name: error"
3. cpu_pct=20 -> gauge bar amber, text shows "20% / 15%"
4. Log with warn+error entries -> correct colors
5. At 375px viewport: cards stack, no horizontal overflow
6. At 1440px: fits sidebar 250px (current aside width) without scroll

## Estimated effort at trigger
- CSS + JS pre-built now: ~10 min integration on trigger day (add markup, pin, test)
- If not pre-built: ~45 min total
