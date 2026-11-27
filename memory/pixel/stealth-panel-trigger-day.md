# Stealth Ops Panel - Trigger-Day Runbook (Pixel)
Updated 2026-11-26 | Status: UI 100% pre-built + inert; gated on BACKEND `/api/stealth/*` (Builder lane).

## Verified current state (measured this pass, 2026-11-26)
- `ui/app.css`: **15** stealth rules present (.stealth-panel + .st-*). Covers every selector stealth.js emits:
  st-card, st-state-{running,success,error}, st-meta, st-dur, st-gauge, st-track, st-fill(.warn), st-pct, st-line, st-lv-{warn,error}. (Hot-note said "17" - actual is 15; all JS-referenced selectors exist. No gaps.)
- `ui/stealth.js`: **59** lines present. All three renderers guard on missing element (`if(!el)return`) -> safe no-op while panel absent from DOM.
- `agent_portal.py`: **NO `/api/stealth/*` routes** (grep 'stealth' = 0 hits). This is the HARD GATE: without it, refreshStealth() 404s on all three fetches and the panel would render empty cards. Do NOT pin-advance markup until these exist.

## What remains (trigger day, ~5 min once backend live)
1. Apply this exact fragment to index.html <aside>, after the goal-bar section:
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
   Also add `<script src="/ui/stealth.js"></script>` AFTER the uploads.js script tag (it uses $ + api from core.js).
2. Pin-advance index.html (memory_mirror.py PIN_FILES): copy new file to
   memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html, set PIN_FILES sha12 (first 12 of sha1) + backup path, commit. NEVER re-apply reverted markup without repinning.
3. Run verification checklist (below).

## Verification checklist (trigger day)
1. GET /api/stealth/jobs -> array => 3 cards render with correct state border-left color.
2. Force one job state=error => red border + aria-label reads "<name>: error".
3. cpu_pct > budget_max_pct(15) => gauge fill amber (.st-fill.warn), text shows "N% / 15%".
4. Log with warn+error entries => .st-lv-warn/.st-lv-error colors applied.
5. @375px: cards stack, no horizontal overflow. @1440px: fits 250px aside without scroll.

## Hand-off to Builder (the gate)
Need these three routes so the pre-built panel has a data source:
- `GET /api/stealth/jobs` -> {jobs:[{name,state,last_run,next_run,duration_ms}]}
- `GET /api/stealth/resources` -> {cpu_pct, mem_mb, budget_max_pct}
- `GET /api/stealth/log?limit=20` -> {entries:[{ts,level,msg}]}
Source data exists: the 3 packaged workflows (wf1/wf2/wf3 under memory/builder/stealth/, all selftest-green). Wire job state from their last-run status.

## Stale auto-loop claim closed (option c)
Builder goal #11 "Package top-3 workflows" is VERIFIED-CLOSED, not open.
Proof: goal_ledger.json agents.builder = {total:11, reached:11, open:0}; memory/goals/builder.md line 11 carries `(verified: 2026-11-25 - wf1 4/4, wf2 4/4, wf3 3/3; README + selftests all green)`. Auto-loop prompts re-listing #11 as open are STALE - do not re-probe.
