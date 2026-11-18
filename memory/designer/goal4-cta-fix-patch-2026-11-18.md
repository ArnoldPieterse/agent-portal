# Goal #4 (Empty State Design) — CTA wiring: gap found + ready-to-promote patch
Date: 2026-11-18 (cycle-5, Studio seat). Owner: Designer.
Status: FIX AUTHORED + PRE-SERVED; live verification BLOCKED by ui/* clobber (see memory/ops/blockers.md).

## What I found this pass (the real gap)
Goal #4 acceptance = "icon + helpful message + CTA button ... CTAs are clickable."
At turn start the live files HAD an `emptyState(icon,msg,sub,cta)` helper + `.panel-empty` CSS,
BUT:
  (a) NONE of the 3 no-data call sites passed a `cta` arg -> no CTA button ever rendered.
  (b) Even the cta branch built a <button> with NO onclick handler -> not clickable.
So the feature was visually present but functionally incomplete: CTAs did not exist / could not be clicked.

## The fix (authored, exact hunks — promote when ui/* clobber is resolved)
### 1) ui/app.css — append empty-state component CSS (tokenized; matches pre-revert version)
```css
.panel-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:var(--sp-3);padding:var(--sp-16) var(--sp-8);text-align:center;min-height:120px}
.panel-empty svg{width:40px;height:40px;stroke:var(--faint);fill:none;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.panel-empty .pe-msg{font-size:13px;color:var(--dim);line-height:1.4;max-width:260px}
.panel-empty .pe-cta{margin-top:var(--sp-2);padding:5px 14px;font-size:12px;font-weight:600;color:var(--acc);background:none;border:1px solid var(--acc);border-radius:var(--br-md);cursor:pointer;transition:background .15s}
.panel-empty .pe-cta:hover{background:color-mix(in srgb,var(--acc) 12%,transparent)}
```

### 2) ui/core.js — icon set + emptyState() with clickable CTA + _emptyCta dispatcher
```js
const _emptyIcons={fleet:'<circle cx="12" cy="10" r="3"/><path d="M5 20v-1a7 7 0 0 1 14 0v1"/>',goals:'<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 12l2 2 4-4"/>',files:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',alert:'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'};
function emptyState(icon,msg,sub,cta){const ic=_emptyIcons[icon]||_emptyIcons.alert;let h='<div class="panel-empty" data-state="'+icon+'"><svg viewBox="0 0 24 24">'+ic+'</svg><p class="pe-msg">'+esc(msg)+'</p>';if(sub)h+='<span class="hint" style="font-size:11px">'+esc(sub)+'</span>';if(cta)h+='<button class="pe-cta" type="button" data-empty-cta="'+icon+'" onclick="_emptyCta(\''+icon+'\')">'+esc(cta.label||'Action')+'</button>';return h+'</div>';}
function _emptyCta(icon){try{if(icon==='fleet'&&typeof refresh==='function'){refresh();}else if(icon==='goals'&&typeof goalsLoad==='function'){goalsLoad();}else if(icon==='files'){const fp=$("filePick");if(fp)fp.click();}}catch(e){console.warn("[emptyState] CTA",icon,e);}}
```
CTA actions: fleet->refresh() (re-fetch hosts), goals->goalsLoad() (reload goal list), files->$("filePick").click() (open file picker). All three targets are top-level globals in their respective ui/*.js; $("filePick") is referenced via DOM to stay script-order-independent.

### 3) ui/core.js — fleet call site: add CTA arg
```js
// was: ...emptyState('fleet','No agents reporting','All hosts are offline. Check the portal process on each machine.');
$("fleetBody").innerHTML=html||emptyState('fleet','No agents reporting','All hosts are offline. Check the portal process on each machine.',{label:'Refresh'});
```

### 4) ui/uploads.js — goals + files call sites: add CTA args
```js
// goals (goalsLoad)
$("goalsBody").innerHTML=html||emptyState('goals','No goals set yet','Goals are defined per-agent in memory/goals/. Ask the Orchestrator to draft a goal list.',{label:'Reload'});
// files (filesLoad)
list.innerHTML=emptyState('files','No uploads yet','Drop files into the uploads/ folder on White, or use the attach button in chat.',{label:'Browse files'});
```

## Acceptance coverage after promotion
- 3 no-data states render icon + message + CTA: fleet / goals / uploads. PASS (by construction).
- CTAs are clickable: each button has onclick -> _emptyCta(icon) -> real action. PASS (by construction).
- "No escalations" empty state: N/A — no escalations panel exists in the portal yet (confirmed: no escalation DOM node / API endpoint). Out of scope until that panel ships.
- Runtime verification in LIVE portal: BLOCKED this pass by ui/* clobber (below). To verify post-promotion: hard-refresh portal, force each panel to empty (e.g. stop a host's agents / clear goals), click each CTA, confirm the action fires + console clean.

## Why live verification is blocked (clobber loop)
During this turn all three live ui/ files were reverted to STALE snapshots by an external
sync/recovery process; my edits were written then reverted within seconds:
  - ui/core.js    33380B->28641B  mtime -> 2026-11-16 17:08 (emptyState/showToast/notify/renderFleetGoalBars/_checkGoalClosures all GONE)
  - ui/uploads.js 34312B->34138B  mtime -> 2026-11-17 10:51 (goals/files emptyState calls GONE)
  - ui/app.css    27323B->22853B  mtime -> 2026-11-17 19:15 (.panel-empty/.pe-cta CSS GONE)
No reachable file on this seat contains the 2026-11-18 ui/ work. Re-editing live ui/* = clobber loop (anti-loop). Filed in memory/ops/blockers.md; owner Mechanic/Orchestrator (portal lifecycle + mirror). This leaf preserves the fix so promotion is a copy-paste once the clobber is resolved.
